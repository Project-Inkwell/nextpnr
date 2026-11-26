# Mapping rules from prjxray to nextpnr

# The eight-LUT slice of an UltraScale+ part (its CLE tiles hold one each):
# z[6:4] the letter (A-H), z[3:0] the kind -- 6LUT, 5LUT, FF, FF2, the FF's
# two input muxes, OUTMUX -- and the slice's own bels at fixed z, as
# nextpnr-xilinx's bbaexport.java numbers them (getBelZoverride).
XCUP_SLICE_BELS = {
    "F7MUX_AB": 0x07, "F7MUX_CD": 0x27, "F7MUX_EF": 0x47, "F7MUX_GH": 0x67,
    "F8MUX_BOT": 0x08, "F8MUX_TOP": 0x48, "F9MUX": 0x09, "CARRY8": 0x0A,
    "CLK1INV": 0x0B, "CLK2INV": 0x4B, "LCLKINV": 0x1B,
    "RST_ABCDINV": 0x0C, "RST_EFGHINV": 0x4C, "HARD0GND": 0x0D,
}
# An UltraScale+ block RAM tile's bels, by type.
XCUP_BRAM_BELS = {
    "RAMBFIFO36E2_RAMBFIFO36E2": 0, "RAMB36E2_RAMB36E2": 1, "FIFO36E2_FIFO36E2": 2,
    "RAMB18E2_U_RAMB18E2": 5, "RAMBFIFO18E2_RAMBFIFO18E2": 8, "RAMB18E2_L_RAMB18E2": 9,
    "FIFO18E2_FIFO18E2": 10,
}

def get_xcup_slice_z(bn):
    subslices = "ABCDEFGH"
    for i, pf in enumerate(["6LUT", "5LUT", "FF", "FF2"]):
        if len(bn) == len(pf) + 1 and bn[1:] == pf and bn[0] in subslices:
            return (subslices.index(bn[0]) << 4) | i
    if bn.startswith("FFMUX") and len(bn) == 7:
        return (subslices.index(bn[5]) << 4) | (5 if bn[6] == "2" else 4)
    if bn.startswith("OUTMUX") and len(bn) == 7:
        return (subslices.index(bn[6]) << 4) | 6
    return XCUP_SLICE_BELS.get(bn, -1)

def get_bel_z_override(bel, default_z):
    s = bel.site
    t = s.tile
    bt = bel.bel_type()
    bn = bel.name()
    if t.tile_type().startswith("CLE") and s.site_type() in ("SLICEL", "SLICEM"):
        return get_xcup_slice_z(bn)
    if t.tile_type() == "BRAM" and bt in XCUP_BRAM_BELS:
        return XCUP_BRAM_BELS[bt]
    if t.tile_type() == "BRAM_L" or t.tile_type() == "BRAM_R":
        is_top18 = (s.primary.site_type() == "RAMB18E1")
        if bt == "RAMBFIFO36E1_RAMBFIFO36E1":
            return 0
        elif bt == "RAMB36E1_RAMB36E1":
            return 1
        elif bt == "FIFO36E1_FIFO36E1":
            return 2
        elif bt == "RAMB18E1_RAMB18E1":
            return (5 if is_top18 else 9)
        elif bt == "FIFO18E1_FIFO18E1":
            return 10
    if s.site_type() == "SLICEL" or s.site_type() == "SLICEM":
        is_upper_site = (s.rel_xy()[0] == 1)
        subslices = "ABCD"
        postfixes = ["6LUT", "5LUT", "FF", "5FF"]
        for i, pf in enumerate(postfixes):
            if len(bn) == len(pf) + 1 and bn[1:] == pf:
                return (64 if is_upper_site else 0) | (subslices.index(bn[0]) << 4) | i
        if bn == "F7AMUX":
            return (0x47 if is_upper_site else 0x07)
        elif bn == "F7BMUX":
            return (0x67 if is_upper_site else 0x27)
        elif bn == "F8MUX":
            return (0x48 if is_upper_site else 0x08)
        elif bn == "CARRY4":
            return (0x4F if is_upper_site else 0x0F)
        # Other bels (e.g. extra xc7 routing bels) can be ignored for nextpnr porpoises
        return -1
    return default_z

def get_bel_type_override(bt):
    if bt.endswith("6LUT") or bt == "LUT_OR_MEM6" or bt == "LUT6":
        return "SLICE_LUTX"
    elif bt.endswith("5LUT") or bt == "LUT_OR_MEM5" or bt == "LUT5":
        return "SLICE_LUTX"
    elif len(bt) == 4 and bt.endswith("FF2"):
        return "SLICE_FFX"
    elif len(bt) == 3 and bt.endswith("FF"):
        return "SLICE_FFX"
    elif bt == "FF_INIT" or bt == "REG_INIT":
        return "SLICE_FFX"

    # An UltraScale+ IO bank's buffers (HDIOB_OUTBUF_M, HPIOB_PAD_S, ...):
    # one type each whichever the bank and side, the pad as a 7-series pad.
    if bt.startswith(("HDIOB_", "HPIOB_")):
        for part in ("PAD", "PULL", "IBUFCTRL", "INBUF", "OUTBUF"):
            if f"_{part}_" in bt + "_":
                return "PAD" if part == "PAD" else f"IOB_{part}"

    iolParts = ["COMBUF_", "IDDR_", "IPFF_", "OPFF_", "OPTFF_", "TFF_"]
    for p in iolParts:
        if bt.startswith(p):
            return "IOL_" + p.replace("_", "")
    if bt.endswith("_VREF"):
        return "IOB_VREF"
    elif bt.endswith("_DIFFINBUF"):
        return "IOB_DIFFINBUF"
    elif bt.startswith("PSS_ALTO_CORE_PAD_"):
        return "PSS_PAD"
    elif bt.startswith("LAGUNA_RX_REG") or bt.startswith("LAGUNA_TX_REG"):
        return "LAGUNA_REGX"
    elif bt.startswith("BSCAN"):
        return "BSCAN"
    elif bt == "BUFGCTRL_BUFGCTRL":
        return "BUFGCTRL"
    elif bt == "RAMB18E2_U_RAMB18E2" or bt == "RAMB18E2_L_RAMB18E2":
        return "RAMB18E2_RAMB18E2"
    else:
        return bt

def get_bel_pin_name_override(bel_type, pin):
    # A slice flip-flop's clock is CK, as a 7-series part names it; an
    # UltraScale+ part names it CLK.
    if get_bel_type_override(bel_type) == "SLICE_FFX" and pin == "CLK":
        return "CK"
    return pin

def include_pip(tile_type, p):
    # A logic tile's LUT route-throughs are the generator's own pips
    # (LUT_ROUTETHRU): a 7-series CLB's, and an UltraScale+ CLE's.
    is_xc7_logic = (tile_type in ("CLBLL_L", "CLBLL_R", "CLBLM_L", "CLBLM_R")) or tile_type.startswith("CLE")
    if p.is_route_thru() and p.src_wire().name().endswith("_CE_INT"):
        return False
    if p.is_route_thru() and is_xc7_logic:
        return False
    if p.is_route_thru() and "TFB" in p.dst_wire().name():
        return False
    if p.src_wire().name().startswith("CLK_BUFG_R_FBG_OUT"):
        return False
    if "CLK_HROW_CK_INT" in p.src_wire().name():
        return False
    # if tile_type.startswith("HCLK_CMT") and "FREQ_REF" in p.dst_wire().name():
    #     return False
    if tile_type.startswith("HCLK_IOI"):
        if "RCLK_BEFORE_DIV" in p.dst_wire().name() and "IMUX" in p.src_wire().name():
            return False
        # NOTE: the fork (nextpnr-xilinx) does NOT filter the *_DMUX <-
        # I2IOCLK_TOP pips, and they are required to route a placed BUFR's
        # dedicated clock input (IOB -> HCLK_IOI -> BUFR.I).  Dropping them
        # here made every BUFR design unroutable ("Failed to route arc ...
        # from IOB_X..INBUF_EN_OUT to BUFR_X..I").  Keep them.
    if "IOI" in tile_type:
        if "CLKB" in p.dst_wire().name() and "IMUX22" in p.src_wire().name():
            return False
        if "OCLKB" in p.dst_wire().name() and "IOI_OCLK_" in p.src_wire().name():
            return False
        if "OCLKM" in p.dst_wire().name() and "IMUX31" in p.src_wire().name():
            return False
    if "CMT_TOP_R" in tile_type:
        if "PLLOUT_CLK_FREQ_BB_REBUFOUT" in p.dst_wire().name():
            return False
        if "MMCM_CLK_FREQ_BB" in p.dst_wire().name():
            return False
    # A block RAM's address can be taken from the block RAM above or below it
    # (BRAM_CASCINBOT_ADDR* / BRAM_CASCINTOP_ADDR*), for a cascaded pair.  The
    # router treats them as ordinary pips: a high-fanout address net (a ROM
    # across hundreds of block RAMs) then reaches a column by entering one block
    # RAM and chaining through the others, because reusing the net's own wires
    # costs nothing; on vc707-litex-romlinux one address bit ran through 29 block
    # RAMs in series, 15 ns.  A cascaded pair's address pins are on one net and
    # reachable through the interconnect like any other, so these pips are not
    # needed.
    if tile_type in ("BRAM_L", "BRAM_R"):
        src = p.src_wire().name()
        if "CASCINBOT_ADDR" in src or "CASCINTOP_ADDR" in src:
            return False
    return True

def is_global_bel(bel):
    bt = bel.bel_type()
    return bt in ("BUFGCTRL_BUFGCTRL", "BUFG_BUFG")
