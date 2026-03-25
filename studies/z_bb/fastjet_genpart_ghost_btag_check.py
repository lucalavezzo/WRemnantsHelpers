import argparse
import glob
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import ROOT

CPP = r"""
#include <ROOT/RVec.hxx>
#include <fastjet/ClusterSequence.hh>
#include <HepPDT/ParticleID.hh>
#include <cmath>
#include <algorithm>

namespace wrem_fastcheck {
using ROOT::VecOps::RVec;

inline bool isBHadronLegacy(int pdgId) {
  int64_t id = std::llabs(static_cast<int64_t>(pdgId));
  if (id < 100) return false;
  if (id >= 1000000000LL) return false;
  int nq1 = static_cast<int>((id / 1000) % 10);
  int nq2 = static_cast<int>((id / 100) % 10);
  int nq3 = static_cast<int>((id / 10) % 10);
  if (nq3 == 0) return false;
  return (nq1 == 5) || (nq2 == 5) || (nq3 == 5);
}

inline bool isBHadronPDT(int pdgId) {
  HepPDT::ParticleID pid(pdgId);
  return pid.isHadron() && pid.hasBottom();
}

inline fastjet::PseudoJet makePJ(float pt, float eta, float phi, float mass) {
  const double px = pt * std::cos(phi);
  const double py = pt * std::sin(phi);
  const double pz = pt * std::sinh(eta);
  const double p2 = px * px + py * py + pz * pz;
  const double e = std::sqrt(std::max(0.0, p2 + double(mass) * double(mass)));
  return fastjet::PseudoJet(px, py, pz, e);
}

RVec<float> ghostBTagSummary(const RVec<float>& pt,
                             const RVec<float>& eta,
                             const RVec<float>& phi,
                             const RVec<float>& mass,
                             const RVec<int>& pdgId,
                             const RVec<int>& status,
                             float jetR = 0.4,
                             float ptMin = 30.f,
                             float absEtaMax = 2.5f) {
  const size_t n = std::min({pt.size(), eta.size(), phi.size(), mass.size(), pdgId.size(), status.size()});
  std::vector<fastjet::PseudoJet> particles;
  particles.reserve(n + 16);

  std::vector<fastjet::PseudoJet> ghostsLegacy;
  std::vector<fastjet::PseudoJet> ghostsPDT;
  ghostsLegacy.reserve(16);
  ghostsPDT.reserve(16);

  constexpr double ghostPt = 1e-20;
  int ghostId = 1;

  for (size_t i = 0; i < n; ++i) {
    const int apid = std::abs(pdgId[i]);

    // Cluster stable visible particles.
    if (status[i] == 1) {
      if (apid == 12 || apid == 14 || apid == 16) continue; // neutrinos
      particles.push_back(makePJ(pt[i], eta[i], phi[i], mass[i]));
      particles.back().set_user_index(0);
    }

    // Build ghost hadrons from status 1/2 to align with current hadron selection.
    if (status[i] != 1 && status[i] != 2) continue;

    if (isBHadronLegacy(apid)) {
      auto g = makePJ(float(ghostPt), eta[i], phi[i], 0.f);
      g.set_user_index(ghostId);
      ghostsLegacy.push_back(g);
    }
    if (isBHadronPDT(apid)) {
      auto g = makePJ(float(ghostPt), eta[i], phi[i], 0.f);
      g.set_user_index(ghostId);
      ghostsPDT.push_back(g);
    }
    ++ghostId;
  }

  auto count_bjets = [&](const std::vector<fastjet::PseudoJet>& ghosts) {
    std::vector<fastjet::PseudoJet> inputs = particles;
    inputs.insert(inputs.end(), ghosts.begin(), ghosts.end());

    fastjet::JetDefinition jetdef(fastjet::antikt_algorithm, jetR);
    fastjet::ClusterSequence cs(inputs, jetdef);
    auto jets = fastjet::sorted_by_pt(cs.inclusive_jets(ptMin));

    int njet = 0;
    int nbjet = 0;
    for (const auto& j : jets) {
      if (std::abs(j.eta()) > absEtaMax) continue;
      ++njet;
      bool hasB = false;
      for (const auto& c : j.constituents()) {
        if (c.user_index() != 0) {
          hasB = true;
          break;
        }
      }
      if (hasB) ++nbjet;
    }
    return std::pair<int,int>{njet, nbjet};
  };

  auto [njetLegacy, nbLegacy] = count_bjets(ghostsLegacy);
  auto [njetPDT, nbPDT] = count_bjets(ghostsPDT);

  const int passLegacy = nbLegacy >= 1 ? 1 : 0;
  const int passPDT = nbPDT >= 1 ? 1 : 0;
  int cat = 0;
  if (passLegacy == 1 && passPDT == 0) cat = 1;
  else if (passLegacy == 0 && passPDT == 1) cat = 2;
  else if (passLegacy == 1 && passPDT == 1) cat = 3;

  // [0]=njetLegacy, [1]=njetPDT, [2]=nbLegacy, [3]=nbPDT, [4]=passLegacy, [5]=passPDT, [6]=cat
  return {float(njetLegacy), float(njetPDT), float(nbLegacy), float(nbPDT), float(passLegacy), float(passPDT), float(cat)};
}

RVec<float> nanoVsReclusteredBJetObs(
    const RVec<float>& GenPart_pt, const RVec<float>& GenPart_eta,
    const RVec<float>& GenPart_phi, const RVec<float>& GenPart_mass,
    const RVec<int>& GenPart_pdgId, const RVec<int>& GenPart_status,
    const RVec<float>& GenJet_pt, const RVec<float>& GenJet_eta,
    const RVec<float>& GenJet_phi, const RVec<float>& GenJet_mass,
    const RVec<unsigned char>& GenJet_hadronFlavour,
    float jetR = 0.4, float ptMin = 30.f, float absEtaMax = 2.5f) {

  auto invalid = []() {
    fastjet::PseudoJet pj(0, 0, 0, 0);
    pj.set_user_index(0);
    return pj;
  };

  auto obs_from_bjets = [&](const std::vector<fastjet::PseudoJet>& bjets_in) {
    std::vector<fastjet::PseudoJet> bjets = bjets_in;
    std::sort(bjets.begin(), bjets.end(), [](const auto& a, const auto& b) { return a.perp() > b.perp(); });
    float n = float(bjets.size());
    float lead_pt = bjets.size() > 0 ? float(bjets[0].perp()) : -1.f;
    float sub_pt = bjets.size() > 1 ? float(bjets[1].perp()) : -1.f;
    float lead_eta = bjets.size() > 0 ? float(bjets[0].eta()) : -99.f;
    float sub_eta = bjets.size() > 1 ? float(bjets[1].eta()) : -99.f;
    float mbb = -1.f;
    float drbb = -1.f;
    if (bjets.size() > 1) {
      const auto p = bjets[0] + bjets[1];
      mbb = float(p.m());
      drbb = float(bjets[0].delta_R(bjets[1]));
    }
    return RVec<float>{n, lead_pt, sub_pt, lead_eta, sub_eta, mbb, drbb};
  };

  std::vector<fastjet::PseudoJet> nano_bjets;
  const size_t nj = std::min({GenJet_pt.size(), GenJet_eta.size(), GenJet_phi.size(), GenJet_mass.size(), GenJet_hadronFlavour.size()});
  for (size_t j = 0; j < nj; ++j) {
    if (GenJet_pt[j] < ptMin) continue;
    if (std::abs(GenJet_eta[j]) > absEtaMax) continue;
    if (int(GenJet_hadronFlavour[j]) != 5) continue;
    nano_bjets.push_back(makePJ(GenJet_pt[j], GenJet_eta[j], GenJet_phi[j], GenJet_mass[j]));
  }
  auto nano_obs = obs_from_bjets(nano_bjets);

  const size_t n = std::min({GenPart_pt.size(), GenPart_eta.size(), GenPart_phi.size(), GenPart_mass.size(), GenPart_pdgId.size(), GenPart_status.size()});
  std::vector<fastjet::PseudoJet> particles;
  std::vector<fastjet::PseudoJet> ghosts;
  particles.reserve(n + 16);
  ghosts.reserve(16);
  int ghostId = 1;
  constexpr double ghostPt = 1e-20;
  for (size_t i = 0; i < n; ++i) {
    const int apid = std::abs(GenPart_pdgId[i]);
    if (GenPart_status[i] == 1) {
      if (apid == 12 || apid == 14 || apid == 16) continue;
      auto p = makePJ(GenPart_pt[i], GenPart_eta[i], GenPart_phi[i], GenPart_mass[i]);
      p.set_user_index(0);
      particles.push_back(p);
    }
    if (GenPart_status[i] != 1 && GenPart_status[i] != 2) continue;
    if (!isBHadronLegacy(apid)) continue;
    auto g = makePJ(float(ghostPt), GenPart_eta[i], GenPart_phi[i], 0.f);
    g.set_user_index(ghostId++);
    ghosts.push_back(g);
  }

  std::vector<fastjet::PseudoJet> inputs = particles;
  inputs.insert(inputs.end(), ghosts.begin(), ghosts.end());
  fastjet::JetDefinition jetdef(fastjet::antikt_algorithm, jetR);
  fastjet::ClusterSequence cs(inputs, jetdef);
  auto jets = fastjet::sorted_by_pt(cs.inclusive_jets(ptMin));
  std::vector<fastjet::PseudoJet> recl_bjets;
  for (const auto& j : jets) {
    if (std::abs(j.eta()) > absEtaMax) continue;
    bool hasB = false;
    for (const auto& c : j.constituents()) {
      if (c.user_index() != 0) { hasB = true; break; }
    }
    if (hasB) recl_bjets.push_back(j);
  }
  auto recl_obs = obs_from_bjets(recl_bjets);

  RVec<float> out;
  out.reserve(14);
  for (auto x : nano_obs) out.push_back(x);
  for (auto x : recl_obs) out.push_back(x);
  return out;
}
}
"""


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--max-files-massive", type=int, default=5)
    p.add_argument("--max-files-massless", type=int, default=5)
    p.add_argument("--max-events", type=int, default=20000)
    p.add_argument("--outdir", default=None)
    return p.parse_args()


def pick_files(pattern, nmax):
    files = sorted(glob.glob(pattern))
    if nmax >= 0:
        files = files[:nmax]
    return files


def make_overlay_plot(nano, recl, bins, xlabel, outpath, logy=False):
    hn, edges = np.histogram(nano, bins=bins)
    hr, _ = np.histogram(recl, bins=bins)
    centers = 0.5 * (edges[:-1] + edges[1:])

    fig, (ax, rax) = plt.subplots(
        2,
        1,
        figsize=(7, 6),
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
        sharex=True,
    )
    ax.step(edges[:-1], hn, where="post", label="Nano GenJet b-tagged", linewidth=1.8)
    ax.step(
        edges[:-1], hr, where="post", label="Reclustered GenPart+ghost-b", linewidth=1.8
    )
    if logy:
        ax.set_yscale("log")
    ax.set_ylabel("Events")
    ax.legend(loc="best")
    ax.grid(alpha=0.2)

    ratio = np.divide(hr, hn, out=np.full_like(hr, np.nan, dtype=float), where=hn > 0)
    rax.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
    rax.step(edges[:-1], ratio, where="post")
    rax.set_ylim(0.5, 1.5)
    rax.set_ylabel("Recl/Nano")
    rax.set_xlabel(xlabel)
    rax.grid(alpha=0.2)

    fig.savefig(outpath + ".png", dpi=220, bbox_inches="tight")
    fig.savefig(outpath + ".pdf", bbox_inches="tight")
    plt.close(fig)


def run_sample(label, files, max_events, outdir):
    if not files:
        raise RuntimeError(f"No files for {label}")

    df = ROOT.RDataFrame("Events", files)
    if max_events > 0:
        df = df.Filter(f"rdfentry_ < {max_events}")
    df = df.Define(
        "fj_obs",
        "wrem_fastcheck::ghostBTagSummary(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass, GenPart_pdgId, GenPart_status)",
    )
    df = df.Define(
        "jet_obs",
        "wrem_fastcheck::nanoVsReclusteredBJetObs(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass, GenPart_pdgId, GenPart_status, GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, GenJet_hadronFlavour)",
    )
    df = df.Define("passLegacy", "int(fj_obs[4])")
    df = df.Define("passPDT", "int(fj_obs[5])")
    df = df.Define("cat", "int(fj_obs[6])")

    nev = int(df.Count().GetValue())
    n_leg = float(df.Sum("passLegacy").GetValue())
    n_pdt = float(df.Sum("passPDT").GetValue())

    hcat = df.Histo1D(("cat", "cat", 4, -0.5, 3.5), "cat").GetValue()
    cats = [hcat.GetBinContent(i + 1) for i in range(4)]

    print(f"[{label}] files={len(files)} events={nev}")
    print(f"[{label}] passLegacy={n_leg} ({(n_leg/nev if nev else 0):.6f})")
    print(f"[{label}] passPDT   ={n_pdt} ({(n_pdt/nev if nev else 0):.6f})")
    print(f"[{label}] cat00={cats[0]} cat10={cats[1]} cat01={cats[2]} cat11={cats[3]}")

    cols = {
        "n_bjets_nano": 0,
        "lead_bjet_pt_nano": 1,
        "sublead_bjet_pt_nano": 2,
        "lead_bjet_eta_nano": 3,
        "sublead_bjet_eta_nano": 4,
        "m_bb_jet_nano": 5,
        "dR_bb_jet_nano": 6,
        "n_bjets_recl": 7,
        "lead_bjet_pt_recl": 8,
        "sublead_bjet_pt_recl": 9,
        "lead_bjet_eta_recl": 10,
        "sublead_bjet_eta_recl": 11,
        "m_bb_jet_recl": 12,
        "dR_bb_jet_recl": 13,
    }
    for name, idx in cols.items():
        df = df.Define(name, f"jet_obs[{idx}]")

    specs = [
        (
            "n_bjets_nano",
            "n_bjets_recl",
            np.arange(-0.5, 6.6, 1.0),
            "n b-jets",
            True,
            "n_bjets",
        ),
        (
            "lead_bjet_pt_nano",
            "lead_bjet_pt_recl",
            np.linspace(0, 300, 61),
            "Leading b-jet pT [GeV]",
            True,
            "lead_bjet_pt",
        ),
        (
            "sublead_bjet_pt_nano",
            "sublead_bjet_pt_recl",
            np.linspace(0, 300, 61),
            "Subleading b-jet pT [GeV]",
            True,
            "sublead_bjet_pt",
        ),
        (
            "lead_bjet_eta_nano",
            "lead_bjet_eta_recl",
            np.linspace(-5, 5, 51),
            "Leading b-jet eta",
            False,
            "lead_bjet_eta",
        ),
        (
            "sublead_bjet_eta_nano",
            "sublead_bjet_eta_recl",
            np.linspace(-5, 5, 51),
            "Subleading b-jet eta",
            False,
            "sublead_bjet_eta",
        ),
        (
            "m_bb_jet_nano",
            "m_bb_jet_recl",
            np.linspace(0, 300, 61),
            "m_bb [GeV]",
            True,
            "m_bb_jet",
        ),
        (
            "dR_bb_jet_nano",
            "dR_bb_jet_recl",
            np.linspace(0, 5, 51),
            "DeltaR_bb",
            True,
            "dR_bb_jet",
        ),
    ]

    os.makedirs(outdir, exist_ok=True)
    for c_nano, c_recl, bins, xlabel, logy, short in specs:
        a_nano = np.array(df.Take["float"](c_nano).GetValue(), dtype=float)
        a_recl = np.array(df.Take["float"](c_recl).GetValue(), dtype=float)
        # keep only valid entries for kinematic plots
        if "n_bjets" not in short:
            a_nano = a_nano[a_nano > -90]
            a_recl = a_recl[a_recl > -90]
        outpath = os.path.join(outdir, f"{label}_nano_vs_recl_{short}")
        make_overlay_plot(a_nano, a_recl, bins, xlabel, outpath, logy=logy)


def main():
    args = parse_args()
    ROOT.DisableImplicitMT()
    ROOT.gInterpreter.Declare(CPP)
    hep.style.use("CMS")

    massive = pick_files(
        "/scratch/submit/cms/wmass/NanoGen/MiNNLO_Zbb_weightsPatch/*.root",
        args.max_files_massive,
    )
    massless = pick_files(
        "/scratch/submit/cms/wmass/NanoAOD/DYJetsToMuMu_H2ErratumFix_PDFExt_TuneCP5_13TeV-powhegMiNNLO-pythia8-photos/NanoV9MCPostVFP_TrackFitV722_NanoProdv6/*/*/*.root",
        args.max_files_massless,
    )

    outdir = args.outdir or os.path.join(
        "/tmp", f"fastjet_genpart_compare_{datetime.now().strftime('%y%m%d_%H%M%S')}"
    )
    run_sample("massive", massive, args.max_events, outdir)
    run_sample("massless", massless, args.max_events, outdir)
    print(f"[done] plots in {outdir}")


if __name__ == "__main__":
    main()
