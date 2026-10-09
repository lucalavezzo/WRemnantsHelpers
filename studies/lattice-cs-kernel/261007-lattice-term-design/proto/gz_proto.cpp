// PROTOTYPE (study code, not production) for the option-B lattice term.
//
// Question: can SCETlib's own AD-kernel function ad::gamma_nu_resummed -- the
// function the cross-section kernel already calls -- serve as the lattice
// CS-kernel evaluator, with clad derivatives in (alpha_s, theta_cusp,
// theta_gnu, lambda_inf_nu, lambda2_nu, lambda4_nu)?
//
// Checks, at the 21 ASWZ b_T values (mu = 2 GeV, the cache.conf settings:
// nf 5, N3LL, alphas_solution = rge_solution = analytic, alphas(91.1876) = 0.118,
// collins_soper4 mu0 with mu0_min = 1, b0_over_bmax = 0, b0_over_bmax_nu = 1,
// tanh_2, lambda = 0):
//   A. kernel value == qT::Gamma_nu::operator() (the class, analytic) [pert, full]
//   B. clad gradient == central FD of the CLASS route in each parameter
//   C. clad Hessian  == central FD of the clad gradient
//   D. print the class value with the EXACT RGE too (what the shipped table used)
//
// GlobalData is staged BY HAND here from the same SCETlib coefficient functions
// Ad_evaluator::_build_global uses (QCD::gamma_cusp_*, Gamma_nu::functor,
// Gamma_nu::_3, extract_affine semantics), because building an Ad_evaluator
// needs a full DrellYan config and its PDF grids. In production the staging is
// Ad_evaluator::global() of the param model's already-built calculation.
#include "scetlib/core/RunningCoupling.hpp"
#include "scetlib/core/QCD.hpp"
#include "scetlib/core/TNPs.hpp"
#include "scetlib/qT/Gamma_nu.hpp"
#include "scetlib/qT/scales_formulas.hpp"
#include "scetlib/qT/ad/ad_kernel.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

using namespace scet;
using namespace scet::qT;

namespace gzproto
{
extern thread_local double g_bT, g_mu0, g_fz_mu0, g_fz_mu;
double gnu_point(const double* p);
double gnu_point_grad(const double* p, double* grad, int n);
double gnu_point_hess(const double* p, double* hess, int n);
}

static const int NF = 5;
static const double MZ = 91.1876;
static const double MU = 2.0;
static const double MU0_MIN = 1.0;
static const int FORM = 1;          // collins_soper4
static const double B0BMAX_NU = 1.0;
enum { I_AS, I_CUSP, I_GNU, I_LINF, I_L2, I_L4, NP };
static const char* NAMES[NP] = {"alphas", "tnp_gamma_cusp", "tnp_gamma_nu",
                                "np_gnu_lambda_inf", "np_gnu_lambda2", "np_gnu_lambda4"};

static Gamma_nu::TNPs make_tnps(double tc, double tn)
{
   Gamma_nu::TNPs t {};
   t.gamma_cusp = TNP_adm(3, TNP::level0, tc);   // n_cusp = run order (variations.py make_tnps)
   t.gamma_nu = TNP_adm(2, TNP::level0, tn);     // n_noncusp = run order - 1
   return t;
}

// ---- class route: qT::Gamma_nu::operator() -----------------------------------
static double class_gnu(const double* p, double bT, bool exact, bool np_on)
{
   RunningCoupling<QCD> alphas(p[I_AS], MZ, N3LL, NF,
                               exact ? Coupling_solution::exact : Coupling_solution::analytic, 1.e-10);
   Gamma_nu gnu(qqbar, N3LL, alphas, NF);
   if (exact)
      gnu.set_rge_type(RGE_solution::exact);
   gnu.set_tnps(make_tnps(p[I_CUSP], p[I_GNU]));
   NP_model_gammanu m;
   m.b0_bmax_nu = B0BMAX_NU;
   m.np_model_nu = NP_model_gammanu::tanh_2;
   m.lambda_inf_nu = np_on ? p[I_LINF] : 0.;
   m.lambda2_nu = p[I_L2];
   m.lambda4_nu = p[I_L4];
   gnu.set_np_model(m);
   const double mu0 = scet::qT::formulas::mu_star(b0<> / bT, MU0_MIN, FORM);
   return gnu(bT, mu0, MU);
}

// ---- stage ad_g by hand (mirror of Ad_evaluator::_build_global, gnu fields) ---
template <typename Eval>
static ad::Affine affine(int ip, Eval&& eval)
{
   const double base = eval(0.);
   return {base, eval(1.) - base, ip};
}

static void stage(const double* p0, bool np_on)
{
   ad::GlobalData& g = ad::ad_g;
   g = ad::GlobalData {};
   g.nf = NF;
   g.run_lvl = static_cast<int>(N3LL) + 1;
   const auto beta = QCD::beta(NF);
   for (int n = 0; n < 4; ++n)
      g.beta[n] = beta(n);
   g.beta[4] = 0.;
   for (int n = 0; n < 5; ++n)
      ad::ad_beta[n] = g.beta[n];
   g.as0_base = p0[I_AS];
   g.ip_as0 = I_AS;
   g.mu0_start = MZ;
   g.color_casimir = QCD::CF;
   for (int n = 0; n < 5; ++n) {
      try {
         g.Gq[n] = affine(I_CUSP, [&](double th) { return QCD::gamma_cusp_quark(NF, TNP_adm(3, TNP::level0, th))(n); });
      } catch (...) { g.Gq[n] = {0., 0., -1}; }
      try {
         g.Guniv[n] = affine(I_CUSP, [&](double th) { return QCD::gamma_cusp_universal(NF, TNP_adm(3, TNP::level0, th))(n); });
      } catch (...) { g.Guniv[n] = {0., 0., -1}; }
   }
   for (int n = 0; n < 3; ++n) {
      try {
         g.gnu[n] = affine(I_GNU, [&](double th) { return Gamma_nu::functor(NF, TNP_adm(2, TNP::level0, th))(n); });
      } catch (...) { g.gnu[n] = {0., 0., -1}; }
   }
   {
      const double coeff = Gamma_nu::_3<QCD::quark>(NF);
      g.gnu[3] = affine(I_GNU, [&](double th) { return TNP_adm(2, TNP::level0, th).apply_n(coeff, 3, 4. * QCD::CF, NF); });
   }
   g.np_gnu_model = static_cast<int>(NP_model_gammanu::tanh_2);
   g.gnu_lam_inf = np_on ? p0[I_LINF] : 0.;
   g.gnu_lam2 = p0[I_L2];
   g.gnu_lam4 = p0[I_L4];
   g.gnu_b0bmax = B0BMAX_NU;
   g.ip_gnu_lam_inf = np_on ? I_LINF : -1;
   g.ip_gnu_lam2 = I_L2;
   g.ip_gnu_lam4 = I_L4;
   g.ip_gnu_b0bmax = -1;
   g.ip_gnu_lam6 = -1;
   g.n_params = NP;
}

static void set_point(double bT)
{
   const double mu0 = scet::qT::formulas::mu_star(b0<> / bT, MU0_MIN, FORM);
   gzproto::g_bT = bT;
   gzproto::g_mu0 = mu0;
   gzproto::g_fz_mu0 = mu0;   // lambda = 0 in cache.conf: freeze-out is the identity
   gzproto::g_fz_mu = MU;
}

int main(int argc, char** argv)
{
   // argv: alphas tc tn linf l2 l4  then b_T values in fm
   if (argc < 8) {
      std::fprintf(stderr, "usage: gz_proto alphas tnp_cusp tnp_gnu linf l2 l4 b_fm...\n");
      return 1;
   }
   double p[NP];
   for (int i = 0; i < NP; ++i)
      p[i] = std::atof(argv[1 + i]);
   const double FM = 5.067730716;
   const double h[NP] = {1e-5, 1e-3, 1e-3, 1e-5, 1e-5, 1e-6};

   double maxA_full = 0., maxA_pert = 0., maxB = 0., maxC = 0.;
   std::printf("# b_fm  zeta_class_analytic  zeta_kernel  zeta_class_exact  zeta_kernel_pert  "
               "grad_clad[6] (gamma_zeta units)\n");
   for (int k = 7; k < argc; ++k) {
      const double b_fm = std::atof(argv[k]);
      const double bT = b_fm * FM;
      set_point(bT);

      // A: value, full and pert
      stage(p, true);
      double grad[NP], hess[NP * NP];
      const double v_kernel = gzproto::gnu_point_grad(p, grad, NP);
      const double v_class = class_gnu(p, bT, false, true);
      const double v_exact = class_gnu(p, bT, true, true);
      stage(p, false);
      const double v_kernel_pert = gzproto::gnu_point(p);
      const double v_class_pert = class_gnu(p, bT, false, false);
      maxA_full = std::fmax(maxA_full, std::fabs(v_kernel - v_class));
      maxA_pert = std::fmax(maxA_pert, std::fabs(v_kernel_pert - v_class_pert));

      // B: clad gradient vs central FD of the class
      stage(p, true);
      for (int i = 0; i < NP; ++i) {
         double q[NP];
         for (int j = 0; j < NP; ++j) q[j] = p[j];
         q[i] = p[i] + h[i];
         const double up = class_gnu(q, bT, false, true);
         q[i] = p[i] - h[i];
         const double dn = class_gnu(q, bT, false, true);
         const double fd = (up - dn) / (2. * h[i]);
         const double rel = std::fabs(grad[i] - fd) / std::fmax(1e-8, std::fabs(fd));
         maxB = std::fmax(maxB, rel);
      }

      // C: clad Hessian vs FD of the clad gradient
      gzproto::gnu_point_hess(p, hess, NP);
      for (int i = 0; i < NP; ++i) {
         double q[NP], gu[NP], gd[NP];
         for (int j = 0; j < NP; ++j) q[j] = p[j];
         q[i] = p[i] + h[i];
         stage(q, true);
         gzproto::gnu_point_grad(q, gu, NP);
         q[i] = p[i] - h[i];
         stage(q, true);
         gzproto::gnu_point_grad(q, gd, NP);
         for (int j = 0; j < NP; ++j) {
            const double fd = (gu[j] - gd[j]) / (2. * h[i]);
            const double rel = std::fabs(hess[i * NP + j] - fd) / std::fmax(1e-6, std::fabs(fd));
            maxC = std::fmax(maxC, rel);
         }
      }
      stage(p, true);

      std::printf("%.3f %.12f %.12f %.12f %.12f", b_fm, 0.5 * v_class, 0.5 * v_kernel, 0.5 * v_exact,
                  0.5 * v_kernel_pert);
      for (int i = 0; i < NP; ++i)
         std::printf(" %.10e", 0.5 * grad[i]);
      std::printf("\n");
      if (k == 7) {
         std::printf("# hessian (gamma_zeta units) at b = %.3f fm, params", b_fm);
         for (int i = 0; i < NP; ++i) std::printf(" %s", NAMES[i]);
         std::printf("\n");
         for (int i = 0; i < NP; ++i) {
            std::printf("#H");
            for (int j = 0; j < NP; ++j) std::printf(" % .6e", 0.5 * hess[i * NP + j]);
            std::printf("\n");
         }
      }
   }
   std::printf("# A max|kernel - class(analytic)| full = %.3e, pert = %.3e (gamma_nu units)\n", maxA_full, maxA_pert);
   std::printf("# B max rel |clad grad - FD(class)| = %.3e\n", maxB);
   std::printf("# C max rel |clad hess - FD(clad grad)| = %.3e\n", maxC);
   return 0;
}
