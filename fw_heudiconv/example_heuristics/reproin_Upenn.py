ORDERED_BIDS_FIELDS = [
  'task', 'acq', 'ce', 'dir', 'rec', 'run'
]


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def parse_protocol(protocol_name):

    #print(protocol_name)

    try:
        if ":" in protocol_name:
            protocol_name = protocol_name[protocol_name.index(":"):]
        if "__" in protocol_name:
            protocol_name = protocol_name[:protocol_name.index("__")]

        parts = protocol_name.split("_")
        directory_suffix = parts.pop(0)

        if "-" not in directory_suffix:
            print("Couldn't find the seqtype and label in", protocol_name)
            return ""

        directory, suffix = directory_suffix.split("-")
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
        bids_name = "{subject}/{session}/" + bids_name
        return bids_name

    except ValueError as e:
        print("Couldn't parse protocol name: %s" % protocol_name)
        print(e)
        return ''


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

        template = parse_protocol(s.series_description)

        if template == '':
            continue
        else:
            key = create_key(template)

        if key in info.keys():
            info[key].append(s.series_id)
        else:
            info[key] = [s.series_id]

    return info
