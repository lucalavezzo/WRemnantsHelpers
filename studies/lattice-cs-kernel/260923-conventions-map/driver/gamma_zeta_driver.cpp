// Standalone driver: evaluate SCETlib's full rapidity anomalous dimension
// gamma_nu(bT, mu0(bT), mu) exactly as qT::Gamma_nu::operator() does in the fit
// configuration, and print gamma_zeta = gamma_nu/2 (pert and NP separately).
//
// Usage: gamma_zeta_driver nf alphas_start mu_start run_order(3|4) mu0_min form b0_bmax_nu mu \
//                          np_model(0=tanh_2,1=tanh_6) lam_inf lam2 lam4 lam6  bT_GeV...
// run_order: 3 -> N3LL (N3+0LL nominal), 4 -> N4LL. alphas running order = run_order.
#include "scetlib/qT/Gamma_nu.hpp"
#include "scetlib/qT/scales_formulas.hpp"
#include "scetlib/core/RunningCoupling.hpp"
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>

using namespace scet;
using namespace scet::qT;

int main(int argc, char** argv)
{
   if (argc >= 2 && std::string(argv[1]) == "coeffs") {
      for (int nf = 3; nf <= 5; ++nf) {
         std::printf("nf %d beta", nf);
         for (double b : {QCD::beta<0>(nf), QCD::beta<1>(nf), QCD::beta<2>(nf), QCD::beta<3>(nf), QCD::beta<4>(nf)}) std::printf(" %.15g", b);
         auto gq = QCD::gamma_cusp_quark(nf);
         std::printf(" cuspq");
         for (int n = 0; n < 4; ++n) std::printf(" %.15g", gq(n));
         std::printf(" gnu %.15g %.15g %.15g\n", Gamma_nu::_1(nf), Gamma_nu::_2(nf), Gamma_nu::_3<QCD::quark>(nf));
      }
      return 0;
   }
   if (argc < 15) { std::fprintf(stderr, "bad args\n"); return 1; }
   const char* env_exact = std::getenv("GZ_EXACT");
   const bool exact = env_exact && std::string(env_exact) == "1";
   int nf          = std::atoi(argv[1]);
   double as_start = std::atof(argv[2]);
   double mu_start = std::atof(argv[3]);
   int iorder      = std::atoi(argv[4]);
   double mu0_min  = std::atof(argv[5]);
   int form        = std::atoi(argv[6]);
   double b0bmaxnu = std::atof(argv[7]);
   double mu       = std::atof(argv[8]);
   int npm         = std::atoi(argv[9]);
   double linf = std::atof(argv[10]), l2 = std::atof(argv[11]), l4 = std::atof(argv[12]), l6 = std::atof(argv[13]);
   Run_order order = iorder == 4 ? N4LL : (iorder == 2 ? NNLL : N3LL);

   RunningCoupling<QCD> alphas(as_start, mu_start, order, nf, exact ? Coupling_solution::exact : Coupling_solution::analytic, 1.e-10);
   Gamma_nu gnu(qqbar, order, alphas, nf);
   if (exact) gnu.set_rge_type(RGE_solution::exact);
   {
      const char* tc = std::getenv("GZ_TNP_CUSP");
      const char* tn = std::getenv("GZ_TNP_NU");
      Gamma_nu::TNPs t {};
      int n_cusp = static_cast<int>(order), n_noncusp = static_cast<int>(order) - 1;   // prod/scetlib_run/variations.py make_tnps
      t.gamma_cusp = TNP_adm(n_cusp, TNP::level0, tc ? std::atof(tc) : 0.);
      t.gamma_nu   = TNP_adm(n_noncusp, TNP::level0, tn ? std::atof(tn) : 0.);
      if (order == N3LL) gnu.set_tnps(t);   // TNPs only wired for the N3+0LL nominal
   }

   NP_model_gammanu np_off;  np_off.lambda_inf_nu = 0.; np_off.b0_bmax_nu = b0bmaxnu;
   NP_model_gammanu np_on;   np_on.b0_bmax_nu = b0bmaxnu;
   np_on.np_model_nu = npm == 1 ? NP_model_gammanu::tanh_6 : NP_model_gammanu::tanh_2;
   np_on.lambda_inf_nu = linf; np_on.lambda2_nu = l2; np_on.lambda4_nu = l4; np_on.lambda6_nu = l6;

   std::printf("# bT_GeVinv mu0 alphas_mu0 alphas_mu gzeta_pert gzeta_np gzeta_full\n");
   for (int i = 14; i < argc; ++i) {
      double bT = std::atof(argv[i]);
      double mu0 = scet::qT::formulas::mu_star(b0<> / bT, mu0_min, form);   // Scale_provider: b0_over_bmax = 0 -> muT = b0/bT
      gnu.set_np_model(np_off);
      double gp = gnu(bT, mu0, mu);
      gnu.set_np_model(np_on);
      double gf = gnu(bT, mu0, mu);
      std::printf("%.8f %.8f %.8f %.8f %.10f %.10f %.10f\n", bT, mu0, alphas(mu0), alphas(mu), 0.5*gp, 0.5*(gf-gp), 0.5*gf);
   }
   return 0;
}
