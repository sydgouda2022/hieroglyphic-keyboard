/**
 * Shared offline native-script suggestion engine, contract v1.
 * No network, no DOM, no side effects, no automatic correction.
 * Dictionary packs are built and legally reviewed separately.
 * This module owns candidate order, NOT any application's input controls.
 */
export const CONTRACT_VERSION = 1;

export function searchKey(text, language) {
  if (typeof text !== 'string') throw new TypeError('Text must be Unicode text');
  if (language === 'egy') return text.normalize('NFC');
  if (language === 'cop') {
    // Fold Coptic supralinear/combining marks ONLY in the search key.
    // Always insert the exact, attested surface string from the source.
    return text.normalize('NFD').toLocaleLowerCase('und').replace(/\p{Mark}/gu, '').normalize('NFC');
  }
  throw new RangeError('Unknown language: ' + String(language));
}

function firstGreaterOrEqual(rows, value) {
  let lo = 0, hi = rows.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (rows[mid].key < value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function allowed(row, {language, stage, dialect}) {
  return row.language === language
    && (!stage || row.stage === stage)
    && (!dialect || row.dialect === dialect || row.dialect === 'both');
}

function rank(row, rawKey, {language, previous, learned, stage, dialect}) {
  const key = row.key ?? searchKey(row.surface, language);
  // Prefix match is a strict prerequisite in v1; contextual bonus reorders
  // attested matches, never fabricates spellings or cross-language hits.
  if (!key.startsWith(rawKey)) return -Infinity;
  const studyCount = Math.min(10000, Math.max(0, Number(learned?.[row.id] || 0)));
  const frequency = Math.min(1e9, Math.max(0, Number(row.frequency || 0)));
  const previousMatches = previous && (row.previous || []).includes(previous);
  return 100000 + (key === rawKey ? 500 : 0)
    + (stage && row.stage === stage ? 100 : 0)
    + (dialect && row.dialect === dialect ? 100 : 0)
    + Math.log1p(frequency) * 8
    + Math.log1p(studyCount) * 40
    + (previousMatches ? 120 : 0)
    - [...row.surface].length * 0.08;
}

/**
 * @param {object} pack - {schema:1,language:'egy'|'cop',rows:[]}
 * Rows are sorted by `key` then `id` at build time, never on each keystroke.
 * @param {string} input - native Unicode signs / Coptic text
 * @param {object} options - stage OR dialect restricts results; not an auto-detect.
 */
export function suggest(pack, input, options={}) {
  if (pack?.schema !== CONTRACT_VERSION || !['egy','cop'].includes(pack.language))
    throw new Error('Incompatible or missing linguistic pack');
  if (!Array.isArray(pack.rows)) throw new Error('Invalid linguistic pack rows');
  if (typeof input !== 'string') throw new TypeError('Input must be a string');
  const limit = options.limit ?? 6;
  if (!Number.isInteger(limit) || limit < 1 || limit > 80) throw new RangeError('Invalid suggestion limit');
  const language = pack.language;
  const own = {id:null, text:input, raw:true, attested:false, sourceId:null,
               sourceRef:null, stage:null, dialect:null};
  if (!input) return [];
  const rawKey = searchKey(input, language);
  const opts={language,stage:options.stage||null,dialect:options.dialect||null,
              previous:options.previous||null,learned:options.learned||{}};
  const candidates = [];
  let exactAttested = false;
  // Search only the indexed prefix span, not the entire corpus.
  for (let i=firstGreaterOrEqual(pack.rows, rawKey); i<pack.rows.length; i++) {
    const row = pack.rows[i];
    if (!row.key.startsWith(rawKey)) break;
    if (!allowed(row, opts)) continue;
    if (row.surface === input) exactAttested = true;
    if (row.surface === input) continue; // raw input remains first, even if attested
    const score=rank(row,rawKey,opts);
    if (Number.isFinite(score)) candidates.push({row,score});
  }
  candidates.sort((a,b) => b.score-a.score || a.row.id.localeCompare(b.row.id));
  const result=[{...own,attested:exactAttested}];
  // Same displayed surface may have multiple separate documented records;
  // maintain their IDs/evidence, do not silently discard distinct attestations.
  for (const {row} of candidates.slice(0,limit-1)) {
    result.push({id:row.id,text:row.surface,raw:false,attested:row.attested === true,
      sourceId:row.sourceId,sourceRef:row.sourceRef,
      stage:row.stage??null,dialect:row.dialect??null,
      lemmaId:row.lemmaId??null,formId:row.formId??null});
  }
  return result;
}

export function assertPack(pack) {
  if (pack?.schema!==CONTRACT_VERSION || !['cop','egy'].includes(pack.language)) throw Error('Bad pack schema');
  const ids=new Set();let prevKey='',prevId='';
  for(const row of pack.rows||[]) {
    if (!row || typeof row.id!=='string' || !row.id || ids.has(row.id))throw Error('Missing/duplicate spelling id');
    if(typeof row.surface!=='string' || !row.surface || row.language!==pack.language)throw Error('Invalid native-script surface');
    if(row.attested!==true || typeof row.sourceId!=='string' || !row.sourceId || !row.sourceRef)throw Error('Missing attestation/provenance');
    if(pack.language==='egy' && !row.stage)throw Error('Egyptian period scope required');
    if(pack.language==='cop' && !row.dialect)throw Error('Coptic dialect required');
    if (row.key!==searchKey(row.surface,pack.language))throw Error('Incorrect normalized index key');
    if(row.key<prevKey || (row.key===prevKey && row.id<prevId))throw Error('Pack must be sorted by search key and id');
    ids.add(row.id);prevKey=row.key;prevId=row.id;
  }
  if (!ids.size) throw Error('Empty linguistic pack');
  return {entries:ids.size,language:pack.language};
}
