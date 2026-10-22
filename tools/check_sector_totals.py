#!/usr/bin/env python3
"""Reconcile sector-element-targets.csv against gazetted weightings.
Non-bonus rows (bonus != 'Y') must sum to the gazetted element weighting and scorecard total.
Expected values below are transcribed from the gazette summary tables (clause noted per entry).
Exit code 1 if any mismatch is not listed in KNOWN_GAZETTE_ISSUES."""
import csv, sys, os, collections
CSV = os.path.join(os.path.dirname(__file__), '..', 'bee', 'sectors', 'data', 'sector-element-targets.csv')

# Composite scorecards: (sector, name) -> (list of CSV scorecard labels, gazetted total, source)
FS = 'FS 2017'
SCORECARDS = {
 ('Construction','Large-Contractor'): (['Large-Contractor'], 105, 'CSC000 8.1: 123 incl. 18 bonus'),
 ('Construction','Large-BEP'): (['Large-BEP'], 106, 'CSC000 8.1: 123 incl. 17 bonus'),
 ('Construction','QSE'): (['QSE (Contractor & BEP)'], 105, 'CSC000 8.2: 110 incl. 5 bonus (27+20+24+29+5)'),
 (FS,'Banks & Life'): (['Large (Table 2a: banks, insurers, exchanges)','Large (all)','Large-Banks&Life','Large-Banks&Life + STI'], 120, 'FS000 8.1'),
 (FS,'Short-term insurers'): (['Large (Table 2a: banks, insurers, exchanges)','Large (all)','Large-Other (STI, exchanges, others)','Large-Banks&Life + STI'], 115, 'FS000 8.1'),
 (FS,'Exchanges & members'): (['Large (Table 2a: banks, insurers, exchanges)','Large (all)','Large-Other (STI, exchanges, others)'], 103, 'FS000 8.1'),
 (FS,'Other institutions'): (['Large-Other (Table 2a variant)','Large (all)','Large-Other (STI, exchanges, others)'], 105, 'FS000 8.1'),
 (FS,'QSFI'): (['QSFI'], 100, 'FS000 8.2'),
 ('AgriBEE','Large'): (['Large'], 119, 'AgriBEE 4.1: 25+19+20+40+15'),
 ('AgriBEE','QSE'): (['QSE'], 110, 'AgriBEE 4.2: 25+15+30+25+15'),
 ('Tourism','Large'): (['Large'], 111, 'TSC000 17.1: 27+19+20+40+5'),
 ('Tourism','QSE'): (['QSE'], 101, 'TSC000 17.2: 26+15+25+30+5'),
 ('ICT','QSE'): (['QSE'], 107, 'AICT600 Statement 600 3.1: 25+15+25+30+12'),
}
# Element weightings: (sector, csv scorecard label, element-prefix) -> expected non-bonus points
ELEMENTS = {
 ('Construction','QSE (Contractor & BEP)','Ownership'):27, ('Construction','QSE (Contractor & BEP)','Management Control'):20,
 ('Construction','QSE (Contractor & BEP)','Skills Development'):24, ('Construction','QSE (Contractor & BEP)','PP&SD'):29,
 ('Construction','QSE (Contractor & BEP)','SED'):5,
 ('Construction','Large-Contractor','PP&SD'):34, ('Construction','Large-BEP','PP&SD'):27,
 ('Construction','Large-Contractor','Skills Development'):21, ('Construction','Large-BEP','Skills Development'):29,
 ('Tourism','QSE','Ownership'):26, ('Tourism','QSE','ESD'):30, ('Tourism','QSE','Skills Development'):25,
 ('Tourism','Large','ESD'):40, ('AgriBEE','Large','ESD'):40, ('AgriBEE','QSE','ESD'):25,
 (FS,'QSFI','ESD'):30, (FS,'Large-Banks&Life','Empowerment Financing'):25,
 ('ICT','QSE','Ownership'):25, ('ICT','QSE','Management Control'):15, ('ICT','QSE','Skills Development'):25,
 ('ICT','QSE','ESD'):30, ('ICT','QSE','SED'):12,
}
# Mismatches where the gazette itself does not reconcile (documented in sector-element-targets.md)
KNOWN_GAZETTE_ISSUES = {
 ('Construction','QSE'): 'CSC605 table prints SED 3 + 2 bonus; CSC000 8.2 prints SED 5 (no bonus). Gazette total 110 holds either way.',
 ('Construction','QSE (Contractor & BEP)','SED'): 'as above',
}

def main():
    pts = collections.defaultdict(float); el = collections.defaultdict(float); bad_num = []
    for i, r in enumerate(csv.DictReader(open(CSV)), start=2):
        try: p = float(r['points'])
        except ValueError: bad_num.append((i, r['points'])); continue
        if r['bonus'] == 'Y': continue
        pts[(r['sector'], r['scorecard'])] += p
        el[(r['sector'], r['scorecard'], r['element'])] += p
    fails = 0; known = 0
    print('SCORECARD TOTALS (non-bonus)')
    for (sec, name), (labels, exp, src) in SCORECARDS.items():
        got = sum(pts[(sec, l)] for l in labels)
        ok = abs(got - exp) < 1e-9
        tag = 'OK' if ok else ('KNOWN-GAZETTE' if (sec, name) in KNOWN_GAZETTE_ISSUES else 'MISMATCH')
        if not ok: fails += tag == 'MISMATCH'; known += tag != 'MISMATCH'
        print(f'  {tag:13} {sec} / {name}: csv={got:g} gazette={exp:g} [{src}]' + (f' -- {KNOWN_GAZETTE_ISSUES[(sec,name)]}' if tag=='KNOWN-GAZETTE' else ''))
    print('ELEMENT WEIGHTINGS (non-bonus)')
    for (sec, sc, pre), exp in ELEMENTS.items():
        got = sum(v for (s, c, e), v in el.items() if s == sec and c == sc and e.startswith(pre))
        ok = abs(got - exp) < 1e-9
        tag = 'OK' if ok else ('KNOWN-GAZETTE' if (sec, sc, pre) in KNOWN_GAZETTE_ISSUES else 'MISMATCH')
        if not ok: fails += tag == 'MISMATCH'; known += tag != 'MISMATCH'
        print(f'  {tag:13} {sec} / {sc} / {pre}: csv={got:g} gazette={exp:g}')
    for i, v in bad_num: print(f'  MISMATCH      non-numeric points at CSV line {i}: {v!r}'); fails += 1
    print(f'RESULT: {fails} mismatch(es), {known} known gazette inconsistency(ies)')
    return 1 if fails else 0

if __name__ == '__main__': sys.exit(main())
