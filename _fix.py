import codecs

for fname in ['game.html', 'dev.html']:
    d = codecs.open(fname, 'r', 'utf-8').read()
    
    # Replace version 2026.1.5 with 2026.1.6 everywhere
    d = d.replace('v=2026.1.5', 'v=2026.1.6')
    d = d.replace('2026.1.5', '2026.1.6')
    
    # Simplify cache-busting: remove sessionStorage guard, just check and redirect
    old_script = 'if(!location.search.includes("v=2026.1.6")){if(!sessionStorage.getItem("_vr")){sessionStorage.setItem("_vr","1");location.replace(location.pathname+"?v=2026.1.6"+location.hash)}}'
    new_script = 'if(!location.search.includes("v=2026.1.6"))location.replace(location.pathname+"?v=2026.1.6"+location.hash)'
    d = d.replace(old_script, new_script)
    
    codecs.open(fname, 'w', 'utf-8').write(d)
    print(fname + ': v2026.1.6, cache-busting simplified')
