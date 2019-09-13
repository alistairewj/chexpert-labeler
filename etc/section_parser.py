
import re


def split_report_into_sections(text):
    p_section = re.compile(
        r'\n ([A-Z ()/,-]+):\s', re.DOTALL)

    sections = list()
    section_names = list()
    section_idx = list()

    idx = 0
    s = p_section.search(text, idx)

    if s:
        sections.append(text[0:s.start(1)])
        section_names.append('preamble')
        section_idx.append(0)

        while s:
            current_section = s.group(1).lower()
            # get the start of the text for this section
            idx_start = s.end()
            # skip past the first newline to avoid some bad parses
            idx_skip = text[idx_start:].find('\n')
            if idx_skip == -1:
                idx_skip = 0

            s = p_section.search(text, idx_start + idx_skip)

            if s is None:
                idx_end = len(text)
            else:
                idx_end = s.start()

            sections.append(text[idx_start:idx_end])
            section_names.append(current_section)
            section_idx.append(idx_start)

    else:
        sections.append(text)
        section_names.append('full report')
        section_idx.append(0)

    section_names = normalize_section_names(section_names)

    if ('impression' not in section_names) & ('findings' not in section_names):
        # create a new section for the final paragraph
        if '\n \n' in sections[-1]:
            sections.append(sections[-1].split('\n \n')[-1])
            sections[-2] = sections[-2].split('\n \n')[0:-1]
            section_names.append('last_paragraph')
            section_idx.append(section_idx[-1] + len(sections[-2]))

    return sections, section_names, section_idx


def normalize_section_names(section_names):
    # first, lower case all
    section_names = [s.lower().strip() for s in section_names]

    frequent_sections = {
        "preamble": "preamble",  # 227885
        "impression": "impression",  # 187759
        "comparison": "comparison",  # 154647
        "indication": "indication",  # 153730
        "findings": "findings",  # 149842
        "examination": "examination",  # 94094
        "technique": "technique",  # 81402
        "history": "history",  # 45624
        "comparisons": "comparison",  # 8686
        "clinical history": "history",  # 7121
        "reason for examination": "indication",  # 5845
        "notification": "notification",  # 5749
        "reason for exam": "indication",  # 4430
        "clinical information": "history",  # 4024
        "exam": "examination",  # 3907
        "clinical indication": "indication",  # 1945
        "conclusion": "impression",  # 1802
        "chest, two views": "chest, two views",  # 1735
        "recommendation(s)": "recommendations",  # 1700
        "type of examination": "examination",  # 1678
        "reference exam": "comparison",  # 347
        "patient history": "history",  # 251
        "addendum": "addendum",  # 183
        "comparison exam": "comparison",  # 163
        "date": "date",  # 108
        "comment": "comment",  # 88
        "findings and impression": "impression",  # 87
        "wet read": "wet read",  # 83
        "comparison film": "comparison",  # 79
        "recommendations": "recommendations",  # 72
        "findings/impression": "impression",  # 47
        "pfi": "history",
        'recommendation': 'recommendations',
        'wetread': 'wet read',
        'ndication': 'impression',  # 1
        'impresson': 'impression',  # 2
        'imprression': 'impression',  # 1
        'imoression': 'impression',  # 1
        'impressoin': 'impression',  # 1
        'imprssion': 'impression',  # 1
        'impresion': 'impression',  # 1
        'imperssion': 'impression',  # 1
        'mpression': 'impression',  # 1
        'impession': 'impression',  # 3
        'findings/ impression': 'impression',  # ,1
        'finding': 'findings',  # ,8
        'findins': 'findings',
        'findindgs': 'findings',  # ,1
        'findgings': 'findings',  # ,1
        'findngs': 'findings',  # ,1
        'findnings': 'findings',  # ,1
        'finidngs': 'findings',  # ,2
        'idication': 'indication',  # ,1
        'reference findings': 'findings',  # ,1
        'comparision': 'comparison',  # ,2
        'comparsion': 'comparison',  # ,1
        'comparrison': 'comparison',  # ,1
        'comparisions': 'comparison'  # ,1
    }

    p_findings = [
        'chest',
        'portable',
        'pa and lateral',
        'lateral and pa',
        'ap and lateral',
        'lateral and ap',
        'frontal and',
        'two views',
        'frontal view',
        'pa view',
        'ap view',
        'one view',
        'lateral view',
        'bone window',
        'frontal upright',
        'frontal semi-upright',
        'ribs'
    ]
    p_findings = re.compile('({})'.format('|'.join(p_findings)))

    main_sections = [
        'impression', 'findings', 'history', 'comparison',
        'addendum'
    ]
    for i, s in enumerate(section_names):
        if s in frequent_sections:
            section_names[i] = frequent_sections[s]
            continue

        main_flag = False
        for m in main_sections:
            if m in s:
                section_names[i] = m
                main_flag = True
                break
        if main_flag:
            continue

        m = p_findings.search(s)
        if m is not None:
            section_names[i] = 'findings'

        # if it looks like it is describing the entire study
        # it's equivalent to findings
        # group similar phrasings for impression

    return section_names
