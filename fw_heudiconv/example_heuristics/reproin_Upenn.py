ORDERED_BIDS_FIELDS = [
  'task', 'acq', 'ce', 'dir', 'rec', 'run'
]


def parse_protocol(protocol_name):

    #print(protocol_name)

    if ":" in protocol_name:
        protocol_name = protocol_name[protocol_name.index(":"):]
    if "__" in protocol_name:
        protocol_name = protocol_name[:protocol_name.index("__")]

    parts = protocol_name.split("_")

    #print(parts)

    directory, suffix = parts.pop(0).split("-")
    bids_name = directory + "/{subject}"
    field_lookup = { key: value for key,value in [part.split("-") for part in parts]}
    if 'ses' in field_lookup:
        bids_name += '_ses-' + field_lookup['ses']
    else:
        bids_name += "_{session}"

    #print(field_lookup)
    for bids_key in ORDERED_BIDS_FIELDS:
        if bids_key in field_lookup:
            bids_name += '_%s-%s' % (bids_key, field_lookup[bids_key])
    bids_name += "_" + suffix
    #print(bids_name)
    return bids_name


## within heuristic
def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    info ={}

    for s in seqinfo:

        key = parse_protocol(s.series_description)
        print(key)

        if key in info.keys():
            info[key].append(s.series_id)
        else:
            info[key] = [s.series_id]

    return info
