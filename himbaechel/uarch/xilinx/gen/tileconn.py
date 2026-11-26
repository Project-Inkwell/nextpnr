import json

def merge_nodes(a, b):
    if a is b:
        return
    for bwire in b.wires:
        bwire.tile.wire_to_node[bwire.index] = a
        a.wires.append(bwire)
    b.wires = []

def apply_nodes(f, d):
    # A node list: a line per node, its wires as "<tile>/<wire>". The nodes
    # exactly, where tileconn.json reduces them to joins by tile type and
    # offset.
    for line in f:
        wires = line.split()
        if len(wires) < 2:
            continue
        first = None
        for tile_wire in wires:
            tile, wire = tile_wire.split("/", 1)
            node = d.tile(tile).wire(wire).node()
            if first is None:
                first = node
            else:
                merge_nodes(first, node)

def apply_tileconn(f, d):

    tj = json.load(f)
    # Restructure to tiletype -> coord offset -> type -> wire_pairs
    ttn = {}
    for entry in tj:
        tile0, tile1 = entry["tile_types"]
        dx, dy = entry["grid_deltas"]
        if tile0 not in ttn:
            ttn[tile0] = {}
        if (dx, dy) not in ttn[tile0]:
            ttn[tile0][dx, dy] = {}
        ttn[tile0][dx, dy][tile1] = entry["wire_pairs"]
    for tile in d.tiles:
        tt = tile.tile_type()
        if tt not in ttn:
            continue
        # Search the neighborhood around a tile
        for dxy, nd in sorted(ttn[tt].items()):
            nx = tile.x + dxy[0]
            ny = tile.y + dxy[1]
            if (nx, ny) not in d.tiles_by_xy:
                continue
            ntile = d.tiles_by_xy[nx, ny]
            ntt = ntile.tile_type()
            if ntt not in nd:
                continue
            # Found a pair with connections
            wc = nd[ntt]
            for wirea, wireb in wc:
                merge_nodes(tile.wire(wirea).node(), ntile.wire(wireb).node())
