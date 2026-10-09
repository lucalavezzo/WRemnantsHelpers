"""Shared definitions for T8: the 2D-lattice-card command derived from NOMSTIFF's OWN meta_info command."""

import shlex

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
XWSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"
CARD_1D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
CARD_2D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_statsyst.hdf5"
OUT = f"{A}/261006_t8_l4nu_lattice2d"
RT = "/work/submit/lavezzo/rabbit-trustconstr"
TASK = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261006-t8-l4nu-lattice2d"
PM = "wremnants.postprocessing.scetlib_ad.SCETlibADParamModel"
# 2026-10-06 10:40: the WRemnants default turned the TMD priors OFF (params.py, lambda2/lambda4/delta_lambda2 -> FREE_PARAMS).
# Every T8 command built after that pins them explicitly (sigma 1 in theta = the old default), like-for-like with NOMSTIFF.
# Commands built before (T8A/T8A2/T8B/T8C5/T8P5, launched on the old default) carry "lambda2_nu=nan,lambda4_nu=nan" only.
PRIORS = "lambda2_nu=nan,lambda4_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1"


def nomstiff_tokens():
    from rabbit import io_tools

    _, meta = io_tools.get_fitresult(NOMSTIFF, None, meta=True)
    return shlex.split(meta["meta_info"]["command"])


def to_2d_card(toks):
    """NOMSTIFF command -> 2D-lattice card, lambda4_nu fitted, both CS priors replaced by the external term.
    Returns (new tokens, list of human-readable changes)."""
    new = list(toks)
    ch = []
    assert new[1] == CARD_1D, new[1]
    new[1] = CARD_2D
    ch.append(f"card {CARD_1D} -> {CARD_2D}")
    i = new.index("--paramModel")
    assert new[i + 1] == PM
    j = i + 2
    found_fp = found_ps = False
    while j < len(new) and not new[j].startswith("-"):
        t = new[j]
        if t.startswith("fit_params="):
            fp = t[len("fit_params=") :].split(",")
            assert "lambda4_nu" not in fp and "lambda2_nu" in fp
            fp.insert(fp.index("lambda2_nu") + 1, "lambda4_nu")
            new[j] = "fit_params=" + ",".join(fp)
            found_fp = True
            ch.append("fit_params += lambda4_nu (after lambda2_nu)")
        elif t.startswith("prior_sigmas="):
            assert t == "prior_sigmas=lambda2_nu=nan", t
            new[j] = "prior_sigmas=" + PRIORS
            found_ps = True
            ch.append(f"prior_sigmas=lambda2_nu=nan -> {PRIORS}")
        j += 1
    assert found_fp and found_ps
    return new, ch
