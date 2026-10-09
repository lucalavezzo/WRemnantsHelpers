// PROTOTYPE (study code, not production): the clad translation unit of a
// "gamma_nu at a point" entry point. It differentiates SCETlib's OWN AD-kernel
// function ad::gamma_nu_resummed (include/scetlib/qT/ad/ad_kernel.hpp), the
// same function node_value() calls for the cross section, with respect to the
// flat parameter vector p. Point data (bT, mu0, fz_mu0, fz_mu) are staged in a
// thread_local struct, exactly like ad_nd for the cross section, because clad
// cannot take struct arguments.
//
// Like src/qT/ad/ad_derivs_clad.cpp this TU includes ONLY ad_kernel.hpp.
#include "scetlib/qT/ad/ad_kernel.hpp"

#include "clad/Differentiator/Differentiator.h"

namespace gzproto
{
thread_local double g_bT = 0., g_mu0 = 0., g_fz_mu0 = 0., g_fz_mu = 0.;

double gnu_point(const double* p)
{
   return scet::qT::ad::gamma_nu_resummed(p, g_bT, g_mu0, g_fz_mu0, g_fz_mu);
}
double gnu_point_h8(const double* p)
{
   return scet::qT::ad::gamma_nu_resummed(p, g_bT, g_mu0, g_fz_mu0, g_fz_mu);
}

double gnu_point_grad(const double* p, double* grad, int n)
{
   static auto s_grad = clad::gradient(gnu_point, "p");
   for (int i = 0; i < n; ++i)
      grad[i] = 0.;
   s_grad.execute(p, grad);
   return gnu_point(p);
}

double gnu_point_hess(const double* p, double* hess, int n)
{
   static auto s_h8 = clad::hessian(gnu_point_h8, "p[0:7]");
   double H[64];
   for (int k = 0; k < 64; ++k)
      H[k] = 0.;
   s_h8.execute(p, H);
   for (int i = 0; i < n; ++i)
      for (int j = 0; j < n; ++j)
         hess[i * n + j] = 0.5 * (H[i * 8 + j] + H[j * 8 + i]);
   return gnu_point(p);
}
} // namespace gzproto
