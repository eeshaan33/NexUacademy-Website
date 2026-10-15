const babel = require('./node_modules/@babel/core');
const fs = require('fs');
const src = fs.readFileSync('src/pages/teacher/CreateTest.js', 'utf8');
try {
  const r = babel.transformSync(src, {
    filename: 'src/pages/teacher/CreateTest.js',
    presets: [['./node_modules/@babel/preset-env', { targets: { esmodules: true } }], './node_modules/@babel/preset-react'],
  });
  console.log('OK, size:', r.code.length);
} catch (e) {
  console.log('ERR:', String(e).slice(0, 2000));
}
