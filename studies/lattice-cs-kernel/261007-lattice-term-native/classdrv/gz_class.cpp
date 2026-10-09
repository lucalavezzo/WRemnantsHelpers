// Reference: SCETlib's qT::Gamma_nu CLASS (not the AD kernel) at the lattice points,
// in the cache.conf configuration (nf 5, N3LL, alphas(91.1876) = alphas, collins_soper4
// mu0 with mu0_min = 1, b0_over_bmax = 0, b0_over_bmax_nu = 1, tanh_2, lambda = 0).
// Prints gamma_zeta = gamma_nu / 2 (full and pert) with 17 digits.
// usage: gz_class alphas tnp_cusp tnp_gnu linf l2 l4 exact(0|1) mu b_fm...
// env GZ_NF (default 5) and GZ_MUSTART (default 91.1876): the coupling is
// RunningCoupling(alphas, GZ_MUSTART, N3LL, GZ_NF) and Gamma_nu uses GZ_NF.
// With GZ_ASMATCH=<mu> the start value is instead alpha_s^(5)(mu) of
// RunningCoupling(alphas, 91.1876, N3LL, 5) and the start scale is mu
// (the "nf identified at mu" flavour-scheme alternative).
// (adapted from 261007-lattice-term-design/proto/gz_proto.cpp class_gnu)
#include "scetlib/core/RunningCoupling.hpp"
#include "scetlib/core/QCD.hpp"
#include "scetlib/core/TNPs.hpp"
#include "scetlib/qT/Gamma_nu.hpp"
#include "scetlib/qT/scales_formulas.hpp"
#include <cstdio>
#include <cstdlib>
using namespace scet;
using namespace scet::qT;
int main(int argc, char** argv)
{
   if (argc < 10) { std::fprintf(stderr, "usage\n"); return 1; }
   const double as = atof(argv[1]), tc = atof(argv[2]), tn = atof(argv[3]);
   const double linf = atof(argv[4]), l2 = atof(argv[5]), l4 = atof(argv[6]);
   const bool exact = atoi(argv[7]) == 1;
   const double MU = atof(argv[8]);
   const double FM = 5.067730716, MZ = 91.1876;
   const int NF = std::getenv("GZ_NF") ? atoi(std::getenv("GZ_NF")) : 5;
   double MUSTART = std::getenv("GZ_MUSTART") ? atof(std::getenv("GZ_MUSTART")) : MZ;
   double AS = as;
   if (std::getenv("GZ_ASMATCH")) {
      MUSTART = atof(std::getenv("GZ_ASMATCH"));
      RunningCoupling<QCD> a5(as, MZ, N3LL, 5, exact ? Coupling_solution::exact : Coupling_solution::analytic, 1.e-10);
      AS = a5(MUSTART);
   }
   for (int k = 9; k < argc; ++k) {
      const double bT = atof(argv[k]) * FM;
      double out[2];
      for (int np_on = 1; np_on >= 0; --np_on) {
         RunningCoupling<QCD> alphas(AS, MUSTART, N3LL, NF,
                                     exact ? Coupling_solution::exact : Coupling_solution::analytic, 1.e-10);
         Gamma_nu gnu(qqbar, N3LL, alphas, NF);
         if (exact) gnu.set_rge_type(RGE_solution::exact);
         Gamma_nu::TNPs t {};
         t.gamma_cusp = TNP_adm(3, TNP::level0, tc);
         t.gamma_nu = TNP_adm(2, TNP::level0, tn);
         gnu.set_tnps(t);
         NP_model_gammanu m;
         m.b0_bmax_nu = 1.0;
         m.np_model_nu = NP_model_gammanu::tanh_2;
         m.lambda_inf_nu = np_on ? linf : 0.;
         m.lambda2_nu = l2;
         m.lambda4_nu = l4;
         gnu.set_np_model(m);
         const double mu0 = scet::qT::formulas::mu_star(b0<> / bT, 1.0, 1);
         out[np_on] = 0.5 * gnu(bT, mu0, MU);
      }
      std::printf("%s %.17e %.17e\n", argv[k], out[1], out[0]);
   }
   return 0;
}
