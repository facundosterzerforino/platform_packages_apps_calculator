#!/usr/bin/env python
"""Offline build of the Android 2.3.6 Calculator for old phones (xt550-libre).

The prebuilt arity-2.1.2.jar from AOSP is not used: the arity engine is
compiled from its author's source (github.com/preda/arithmetic, Apache 2.0,
commit 7327763, version 2.1.6). The APK is renamed to org.librecalculadora so
it can be installed as a normal app next to (or instead of) the system one.
"""
import argparse, hashlib, os, pathlib, shutil, subprocess, zipfile

ARITY_COMMIT = '7327763'
PACKAGE = 'org.librecalculadora'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for a in ('--jdk', '--build-tools', '--android-jar', '--arity-src', '--keystore', '--storepass-file'):
        p.add_argument(a, required=True)
    p.add_argument('--alias', default='music')
    a = p.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    for secret in (a.keystore, a.storepass_file):
        if pathlib.Path(secret).resolve().is_relative_to(root):
            raise SystemExit('Signing files must be outside the source tree')
    arity = pathlib.Path(a.arity_src)
    head = subprocess.run(['git', '-C', str(arity), 'rev-parse', '--short=7', 'HEAD'],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != ARITY_COMMIT:
        raise SystemExit('arity source must be at commit ' + ARITY_COMMIT)
    sfx = '.exe' if os.name == 'nt' else ''
    jdk, bt = pathlib.Path(a.jdk), pathlib.Path(a.build_tools)
    java, javac = jdk / 'bin' / ('java' + sfx), jdk / 'bin' / ('javac' + sfx)
    aapt, align = bt / ('aapt' + sfx), bt / ('zipalign' + sfx)
    d8, signer = bt / 'lib' / 'd8.jar', bt / 'lib' / 'apksigner.jar'
    out = root / 'build'
    if out.exists(): shutil.rmtree(out)
    for d in ('gen', 'classes', 'dex'): (out / d).mkdir(parents=True)
    run = lambda *c: subprocess.run([str(x) for x in c], cwd=root, check=True)
    common = ('-M', root / 'AndroidManifest.xml', '-S', root / 'res', '-I', a.android_jar,
              '--min-sdk-version', '9', '--target-sdk-version', '10',
              '--version-code', '1', '--version-name', '2.3.6-xt550')
    run(aapt, 'package', '-f', '-m', '-J', out / 'gen', *common)
    srcs = sorted((root / 'src').rglob('*.java')) + sorted((out / 'gen').rglob('*.java'))
    srcs += [f for f in sorted((arity / 'src').rglob('*.java')) if f.name != 'UnitTest.java']
    run(javac, '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-g:none', '-nowarn', '-Xlint:-options',
        '-bootclasspath', a.android_jar, '-d', out / 'classes', *srcs)
    run(java, '-cp', d8, 'com.android.tools.r8.D8', '--release', '--min-api', '9', '--lib', a.android_jar,
        '--output', out / 'dex', *sorted((out / 'classes').rglob('*.class')))
    unsigned, aligned, apk = out / 'unsigned.apk', out / 'aligned.apk', out / 'Calculadora.apk'
    run(aapt, 'package', '-f', '-c', 'es,en,mdpi,hdpi', '--rename-manifest-package', PACKAGE, *common, '-F', unsigned)
    with zipfile.ZipFile(unsigned, 'a', zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo('classes.dex', date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, (out / 'dex/classes.dex').read_bytes())
    run(align, '-f', '4', unsigned, aligned)
    run(java, '-jar', signer, 'sign', '--ks', a.keystore, '--ks-key-alias', a.alias, '--ks-pass', 'file:' + a.storepass_file,
        '--min-sdk-version', '9', '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'false', '--v3-signing-enabled', 'false',
        '--out', apk, aligned)
    run(java, '-jar', signer, 'verify', '--min-sdk-version', '9', apk)
    print('APK:', apk, apk.stat().st_size, 'bytes, SHA256', hashlib.sha256(apk.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
