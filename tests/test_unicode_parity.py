
import json
import pathlib
import random
import subprocess
import unittest
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hieroglyphic_unicode import native_word

class UnicodeParityTests(unittest.TestCase):
    def test_python_compiler_and_js_runtime_match_on_unicode_grammar(self):
        rng=random.Random(20261025)
        atoms=['𓀀','𓄿','𓈖','𓐰','𓐱','𓐲','𓐳','𓐷','𓐸','𓐹','𓐺','𓐻',
               '𓑀','𓑁','𓑂','𓑃','𓑄','𓑅','𓑆','𓑇','𓑈','𓑉','𓑊','𓑋','𓑌',
               '𓑍','𓑎','𓑏','𓑑','n','ⲛ',' ','\u200d']
        samples=['','𓀀','𓄿𓈖','𓀀𓐱𓀁','𓐱','nfr','𓄿𓐱','𓐷𓀀𓐸',
                 '𓐳𓀀𓐴','𓐷𓀀𓐹','𓄿𓑃','𓄿'*257]
        for _ in range(350):
            samples.append(''.join(rng.choice(atoms) for _ in range(rng.randrange(1,14))))
        javascript=(
            "import {validEgyptianWord} from './src/lexicon_install.mjs';"
            "let input='';"
            "for await (const chunk of process.stdin) input+=chunk;"
            "process.stdout.write(JSON.stringify(JSON.parse(input).map(validEgyptianWord)));"
        )
        p=subprocess.run(['node','--input-type=module','-e',javascript],
                         input=json.dumps(samples,ensure_ascii=False),encoding='utf-8',
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,timeout=15,check=True)
        self.assertEqual(json.loads(p.stdout),[native_word(x) for x in samples])
if __name__=='__main__':unittest.main()
