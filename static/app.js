
/* 风格库元数据：value + 显示名 + 简述（网页与卡片共用） */
var STYLE_LIST = [
  {v:'default', t:'默认', d:'浅灰渐变底 + 白卡片，中性干净，适合长时间阅读'},
  {v:'glass', t:'玻璃', d:'Glassmorphism 磨砂玻璃：半透明 + 模糊光晕，通透轻盈，现代感强'},
  {v:'matte', t:'磨砂', d:'雾面噪点玻璃：哑光颗粒质感，柔和低调不刺眼'},
  {v:'liquid', t:'液态玻璃', d:'高光水感玻璃：顶部高光 + 流动光泽，像液态水膜'},
  {v:'material', t:'卡片风', d:'Material 卡片层级：深灰底 + 白色圆角卡 + 投影，就是原"稳部落"风格'},
  {v:'aurora', t:'极光', d:'Aurora UI：深空渐变 + 紫粉蓝弥散光带，梦幻空灵，适合晚间阅读'},
  {v:'dark', t:'暗夜', d:'Dark Mode 纯深色：夜间护眼，卡片自动反白'},
  {v:'paper', t:'纸张', d:'暖白纸纹背景：柔和耐读，像纸质书页'},
  {v:'neo', t:'新拟态', d:'Neumorphism 软浮雕：同色系内凹外凸阴影，立体柔和'},
  {v:'minimal', t:'极简', d:'Minimalist 纯白极简：只有文字和留白，专注内容本身'},
  {v:'brutalism', t:'粗野', d:'Brutalism 粗野主义：白底黑框 + 4px 硬阴影，原始网页感'},
  {v:'neobrutalism', t:'新野兽派', d:'Neo-Brutalism：奶油底 + 粗黑描边 + 硬阴影，鲜明活泼'},
  {v:'clay', t:'黏土', d:'Claymorphism 黏土拟态：奶油色 + 超大圆角，软糯可爱'},
  {v:'soft', t:'柔和', d:'Soft UI：大圆角 + 低饱和柔和阴影，温和舒适'},
  {v:'gradient', t:'渐变', d:'Modern Gradient：紫蓝粉多彩渐变，绚丽现代'},
  {v:'tech', t:'科技', d:'Abstract Tech：深蓝黑 HUD + 网格光晕，赛博科技感'},
  {v:'memphis', t:'孟菲斯', d:'Memphis 孟菲斯：几何色块 + 圆点装饰，80 年代复古活泼'},
  {v:'retro', t:'复古', d:'Retro：奶油米 + 噪点颗粒 + 暖调描边，怀旧温暖'},
  {v:'hacker', t:'黑客', d:'Hacker：纯黑 + 荧光绿网格，极客终端风'},
  {v:'nudy', t:'裸感', d:'Nudy：米杏奶咖低饱和色，高级简约轻奢'},
  {v:'stripe', t:'Stripe', d:'紫调渐变网格 + 精致投影，商业科技（Stripe 官网风）'},
  {v:'notion', t:'Notion', d:'白底 + 微边框文档风，像 Notion 笔记，干净专注'},
  {v:'bento', t:'便当', d:'Bento：圆角模块卡 + 彩色点缀，精致整洁'},
  {v:'organic', t:'有机', d:'Organic：大地色渐变 + 柔和圆角，自然有机感'},
  {v:'editorial', t:'杂志', d:'Editorial：纸感底色 + 衬线标题 + 黑细线，高端杂志排版'},
  {v:'bgimg', t:'自定义图', d:'上传自己的图片做网页背景，可调居中/扩展/裁剪'}
];
/* 图表主题色预设（深端/浅端，柱状图渐变+互动标签+rk圆标+词云主色） */
var CHART_COLORS = [
  {v:'red', c1:'#e6162d', c2:'#ff9a9e', t:'🍒 绯红', d:'默认色：红粉渐变，热情醒目'},
  {v:'blue', c1:'#2b6de0', c2:'#9ec5ff', t:'💧 蔚蓝', d:'蓝青渐变，清爽冷静'},
  {v:'green', c1:'#1f9d55', c2:'#8fe6b0', t:'🌿 翠绿', d:'绿松渐变，自然平和'},
  {v:'purple', c1:'#7b3ff2', c2:'#c9a6ff', t:'🍇 紫罗兰', d:'紫粉渐变，梦幻高级'},
  {v:'orange', c1:'#f07800', c2:'#ffc08a', t:'🍊 橙阳', d:'橙黄渐变，温暖活力'},
  {v:'teal', c1:'#0fa5a0', c2:'#8fe8e0', t:'🐬 青碧', d:'青绿渐变，通透清凉'},
  {v:'pink', c1:'#e0488e', c2:'#ff9cc6', t:'🌸 樱粉', d:'粉紫渐变，甜美柔和'},
  {v:'slate', c1:'#455a74', c2:'#a8c0d8', t:'🪨 石板', d:'蓝灰渐变，沉稳低调'}
];
/* 旧版本存储值映射到新风格ID */
var OLD_MAP = {frosted:'glass', stablog:'material', plain:'default'};
function normStyle(s){ return OLD_MAP[s] || s; }

var pageStyle = normStyle(localStorage.getItem('wb_pageStyle')) || 'default';
var cardStyle = normStyle(localStorage.getItem('wb_cardStyle')) || 'default';
// 🔗 主题联动：锁定后卡片背景跟随网页背景
var linkTheme = localStorage.getItem('wb_linkTheme') === '1';
var chartColor = localStorage.getItem('wb_chartColor') || 'red';
var pageStr = parseInt(localStorage.getItem('wb_pageStr') || '55');
var cardStr = parseInt(localStorage.getItem('wb_cardStr') || '70');
var bgUrl = localStorage.getItem('wb_bgUrl') || '';
var bgFit = localStorage.getItem('wb_bgFit') || 'cover';
var wrapW = parseInt(localStorage.getItem('wb_wrapW') || '720');
var fontS = parseInt(localStorage.getItem('wb_fontS') || '15');
var fontF = localStorage.getItem('wb_fontF') || 'default';
var fontCustom = localStorage.getItem('wb_fontCustom') || '';
/* 字体库：value -> CSS font-family */
var FONT_LIST = {
  default: "'Microsoft YaHei',system-ui,sans-serif",
  yahei: "'Microsoft YaHei','PingFang SC',sans-serif",
  song: "'SimSun','Songti SC',serif",
  kai: "'KaiTi','Kaiti SC','STKaiti',serif",
  hei: "'SimHei','Heiti SC',sans-serif",
  yuan: "'YouYuan','Yuanti SC',sans-serif",
  mono: "'Consolas','Courier New',monospace",
  georgia: "'Georgia','Times New Roman',serif"
};

/* 动态生成两个维度的选项按钮 */
function buildOpts(){
  var pageHtml = '', cardHtml = '', chartHtml = '';
  STYLE_LIST.forEach(function(s){
    pageHtml += '<div class="opt" data-v="' + s.v + '" title="' + s.d + '">' + s.t + '</div>';
    if (s.v !== 'bgimg') cardHtml += '<div class="opt" data-v="' + s.v + '" title="' + s.d + '">' + s.t + '</div>';
  });
  CHART_COLORS.forEach(function(s){
    chartHtml += '<div class="opt chart-opt" data-v="' + s.v + '" title="' + s.d + '">'
               + '<span class="swatch" style="background:linear-gradient(135deg,' + s.c1 + ',' + s.c2 + ')"></span>'
               + s.t + '</div>';
  });
  document.getElementById('pageOpts').innerHTML = pageHtml;
  document.getElementById('cardOpts').innerHTML = cardHtml;
  document.getElementById('chartOpts').innerHTML = chartHtml;
}

function applyStyles(){
  // 网页背景类：玻璃三兄弟共用一个光晕底图
  var pageCls = {default:'', glass:'glow', matte:'glow', liquid:'glow', bgimg:'useBg'};
  var cls = pageCls[pageStyle] || pageStyle;
  document.body.className = cls;
  // 自定义图片：应用背景图 + 布局 + 遮罩
  if (pageStyle === 'bgimg' && bgUrl) {
    var sizeMap = {contain:'contain', cover:'cover', fill:'100% 100%'};
    document.body.style.backgroundImage = "url('" + bgUrl + "')";
    document.body.style.backgroundSize = sizeMap[bgFit] || 'cover';
    document.body.style.setProperty('--bg-veil-op', (pageStr/100*0.75).toFixed(2));
  } else {
    document.body.style.backgroundImage = '';
  }
  // 光晕遮罩强度（玻璃三兄弟才显示，受网页强度滑条控制）
  var veil = document.querySelector('.glow-veil');
  if (veil) veil.style.opacity = (['glass','matte','liquid'].indexOf(pageStyle) >= 0) ? (pageStr/100) : 0;
  document.documentElement.style.setProperty('--glow-op', (pageStr/100).toFixed(2));
  // 🔗 联动：锁定后卡片背景 = 网页背景（自定义背景图没有对应卡片，退回 default）
  if (linkTheme) {
    var want = (pageStyle === 'bgimg') ? 'default' : pageStyle;
    if (cardStyle !== want) {
      cardStyle = want;
      localStorage.setItem('wb_cardStyle', cardStyle);
    }
  }
  // 卡片风格（微博卡片 + 页面标题框）
  var cards = document.querySelectorAll('.card');
  cards.forEach(function(c){ c.className = 'card ' + cardStyle; });
  var heads = document.querySelectorAll('.view-head');
  heads.forEach(function(h){ h.className = 'view-head ' + cardStyle; });
  // 锁定时把卡片那一组选项置灰
  var cardRow = document.getElementById('cardOpts');
  if (cardRow) {
    cardRow.style.opacity = linkTheme ? '.45' : '1';
    cardRow.style.pointerEvents = linkTheme ? 'none' : '';
  }
  var lockBtn = document.getElementById('linkTheme');
  if (lockBtn) {
    lockBtn.textContent = linkTheme ? '🔗' : '🔀';
    lockBtn.title = linkTheme ? '已联动：文本框背景跟随网页背景（点击解开）'
                             : '未联动：可自由混搭（点击锁定）';
    lockBtn.classList.toggle('on', linkTheme);
  }
  // 卡片强度（玻璃三兄弟模糊/通透）
  var blur = 4 + cardStr * 0.28;
  var alpha = 0.30 + cardStr * 0.0065;
  document.documentElement.style.setProperty('--card-blur', blur.toFixed(1) + 'px');
  document.documentElement.style.setProperty('--card-alpha', alpha.toFixed(2));
  // 布局：宽度 + 字号 + 字体
  document.documentElement.style.setProperty('--wrap-w', wrapW + 'px');
  document.documentElement.style.setProperty('--font-size', fontS + 'px');
  var fam = applyFontFamily();
  if (fontF === 'custom') { loadFontList(); }
  document.documentElement.style.setProperty('--font-family', fam);
  // 自定义输入行的显隐
  var fcRow = document.getElementById('fontCustomRow');
  if (fcRow) fcRow.style.display = (fontF === 'custom') ? '' : 'none';
  // 图表主题色（同时驱动界面强调色联动：按钮/链接/滑块/标题/分页）
  var cc = CHART_COLORS.find(function(s){ return s.v === chartColor; });
  if (cc) {
    document.documentElement.style.setProperty('--chart-c1', cc.c1);
    document.documentElement.style.setProperty('--chart-c2', cc.c2);
    // 派生色：浅底 / 更浅hover底 / 暗底 / 亮字（HSL 提亮降饱和，保证彩色不灰）
    function mixWhite(hex, p){
      var r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
      r=Math.round(r+(255-r)*p);g=Math.round(g+(255-g)*p);b=Math.round(b+(255-b)*p);
      return '#'+[r,g,b].map(function(x){return x.toString(16).padStart(2,'0');}).join('');
    }
    function brighten(hex){
      var r=parseInt(hex.slice(1,3),16)/255,g=parseInt(hex.slice(3,5),16)/255,b=parseInt(hex.slice(5,7),16)/255;
      var mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(mx+mn)/2,d=mx-mn,s=d?(l>0.5?d/(2-mx-mn):d/(mx+mn)):0,h=0;
      if(d){if(mx===r)h=((g-b)/d)%6;else if(mx===g)h=(b-r)/d+2;else h=(r-g)/d+4;h*=60;if(h<0)h+=360;}
      var L=0.72,S=Math.min(1,s*0.55),c=(1-Math.abs(2*L-1))*S,x=c*(1-Math.abs((h/60)%2-1)),m=L-c/2,R,G2,B2;
      if(h<60){R=c;G2=x;B2=0;}else if(h<120){R=x;G2=c;B2=0;}else if(h<180){R=0;G2=c;B2=x;}else if(h<240){R=0;G2=x;B2=c;}else if(h<300){R=x;G2=0;B2=c;}else{R=c;G2=0;B2=x;}
      return '#'+[Math.round((R+m)*255),Math.round((G2+m)*255),Math.round((B2+m)*255)].map(function(v){return v.toString(16).padStart(2,'0');}).join('');
    }
    document.documentElement.style.setProperty('--accent-soft', mixWhite(cc.c1, 0.93));
    document.documentElement.style.setProperty('--accent-soft2', mixWhite(cc.c1, 0.97));
    document.documentElement.style.setProperty('--accent-dark', mixWhite(cc.c1, 0.10));
    document.documentElement.style.setProperty('--accent-bright', brighten(cc.c1));
  }
  // 上传行显隐
  var up = document.getElementById('bgUploadRow');
  if (up) up.style.display = (pageStyle === 'bgimg') ? '' : 'none';
  // 选项高亮
  document.querySelectorAll('.row').forEach(function(row){
    var t = row.getAttribute('data-target');
    var cur = (t === 'page') ? pageStyle : (t === 'card') ? cardStyle : (t === 'chart') ? chartColor : bgFit;
    row.querySelectorAll('.opt').forEach(function(o){
      o.classList.toggle('on', o.getAttribute('data-v') === cur);
    });
  });
  document.getElementById('pageStr').value = pageStr;
  document.getElementById('cardStr').value = cardStr;
  document.getElementById('pageStrV').textContent = pageStr;
  document.getElementById('cardStrV').textContent = cardStr;
  document.getElementById('wrapW').value = wrapW;
  document.getElementById('fontS').value = fontS;
  document.getElementById('fontF').value = fontF;
  var _fc = document.getElementById('fontCustom');
  if (_fc) {
    _fc.value = fontCustom;
    if (fontF === 'custom') {
      loadFontList();
      if (!_fc._bound) { _fc.addEventListener('focus', loadFontList); _fc._bound = true; }
    }
  }
  document.getElementById('wrapWV').textContent = wrapW;
  document.getElementById('fontSV').textContent = fontS;
  showStyleTip();
}
/* 风格说明条：显示当前网页/卡片风格的特点 */
function showStyleTip(){
  var tip = document.getElementById('styleTip');
  if (!tip) return;
  var p = null, c = null;
  STYLE_LIST.forEach(function(s){
    if (s.v === pageStyle) p = s;
    if (s.v === cardStyle) c = s;
  });
  var html = '';
  if (p) html += '<b>网页</b> ' + p.t + ' — ' + p.d + '<br>';
  if (c) html += '<b>卡片</b> ' + c.t + ' — ' + c.d;
  tip.innerHTML = html;
  tip.classList.add('on');
}
function toggleSettings(){ document.getElementById('settingsPanel').classList.toggle('open'); }
// 点击外观设置面板以外的区域自动关闭（窄屏不被"硬控"）
document.addEventListener('click', function(e){
  var panel = document.getElementById('settingsPanel');
  var btn = document.getElementById('openSet');
  if (!panel || !panel.classList.contains('open')) return;
  if (btn && btn.contains(e.target)) return;
  if (panel.contains(e.target)) return;
  panel.classList.remove('open');
});
// dropzone 点击触发文件选择
document.getElementById('bgDrop').addEventListener('click', function(){ document.getElementById('bgFile').click(); });
// 风格选项事件委托：buildOpts() 动态生成的 .opt 也在范围内
document.addEventListener('click', function(e){
  var o = e.target;
  while (o && !(o.classList && o.classList.contains('opt'))) o = o.parentNode;
  if (!o) return;
  var row = o.parentNode;
  var t = row.getAttribute('data-target');
  var v = o.getAttribute('data-v');
  if (t === 'page') {
    pageStyle = v; localStorage.setItem('wb_pageStyle', v);
    if (linkTheme) {
      cardStyle = (v === 'bgimg') ? 'default' : v;
      localStorage.setItem('wb_cardStyle', cardStyle);
    }
  }
  else if (t === 'card') { cardStyle = v; localStorage.setItem('wb_cardStyle', v); }
  else if (t === 'chart') { chartColor = v; localStorage.setItem('wb_chartColor', v); }
  else if (t === 'bgfit') { bgFit = v; localStorage.setItem('wb_bgFit', v); }
  applyStyles();
});
var _lockBtn = document.getElementById('linkTheme');
if (_lockBtn) {
  _lockBtn.addEventListener('click', function(){
    linkTheme = !linkTheme;
    localStorage.setItem('wb_linkTheme', linkTheme ? '1' : '0');
    applyStyles();
  });
}

document.getElementById('pageStr').addEventListener('input', function(){
  pageStr = parseInt(this.value);
  document.getElementById('pageStrV').textContent = pageStr;
  localStorage.setItem('wb_pageStr', pageStr);
  applyStyles();
});
document.getElementById('cardStr').addEventListener('input', function(){
  cardStr = parseInt(this.value);
  document.getElementById('cardStrV').textContent = cardStr;
  localStorage.setItem('wb_cardStr', cardStr);
  applyStyles();
});
document.getElementById('wrapW').addEventListener('input', function(){
  wrapW = parseInt(this.value);
  document.getElementById('wrapWV').textContent = wrapW;
  localStorage.setItem('wb_wrapW', wrapW);
  applyStyles();
});
document.getElementById('fontS').addEventListener('input', function(){
  fontS = parseInt(this.value);
  document.getElementById('fontSV').textContent = fontS;
  localStorage.setItem('wb_fontS', fontS);
  applyStyles();
});
/* 自定义字体：从 /api/fonts 拉本机字体列表，填进 datalist */
/* 根据当前设置算出 font-family（自定义时同时给出中文名/英文名） */
function applyFontFamily(){
  var fam = FONT_LIST[fontF] || FONT_LIST['default'];
  if (fontF === 'custom') {
    var raw = (fontCustom || '').trim();
    if (raw) {
      var parts = [];
      raw.split(',').forEach(function (x) {
        x = x.trim().replace(/^["']|["']$/g, '').replace(/"/g, '');
        if (!x) return;
        parts.push('"' + x + '"');
        var alt = _fontMap[x];
        if (alt && alt !== x) parts.push('"' + alt + '"');
      });
      fam = parts.length
        ? (parts.join(',') + ',"Microsoft YaHei",system-ui,sans-serif')
        : FONT_LIST['default'];
    }
  }
  document.documentElement.style.setProperty('--font-family', fam);
  return fam;
}

var _fontsLoaded = false;
var _fontMap = {};      /* 显示名 <-> 家族名 双向映射 */
function loadFontList(){
  if (_fontsLoaded) return;
  _fontsLoaded = true;
  var dl = document.getElementById('wbFontDatalist');
  if (!dl) return;
  fetch('/api/fonts').then(function(r){ return r.json(); }).then(function(j){
    var frag = document.createDocumentFragment();
    (j.fonts || []).forEach(function(f){
      var disp = f.display || f.family;
      if (disp !== f.family) { _fontMap[disp] = f.family; _fontMap[f.family] = f.family; }
      _fontMap[f.family] = f.family;
      var opt = document.createElement('option');
      opt.value = disp;                       /* 下拉里显示用户眼熟的名字 */
      opt.label = (disp === f.family ? disp : (disp + '  ·  ' + f.family))
                  + (f.style && f.style !== 'Regular' ? ('  ·  ' + f.style) : '');
      frag.appendChild(opt);
    });
    dl.appendChild(frag);
    if (fontF === 'custom') applyFontFamily();
  }).catch(function(){ /* 静默失败，手填也能用 */ });
}

document.getElementById('fontCustom').addEventListener('input', function(){
  fontCustom = this.value;
  localStorage.setItem('wb_fontCustom', fontCustom);
  applyStyles();
});

document.getElementById('fontF').addEventListener('change', function(){
  fontF = this.value;
  localStorage.setItem('wb_fontF', fontF);
  applyStyles();
});
// 自定义图片上传
document.getElementById('bgFile').addEventListener('change', function(){
  var file = this.files[0];
  if (!file) return;
  if (file.size > 10*1024*1024) { alert('图片不能超过 10MB'); return; }
  var fd = new FormData();
  fd.append('file', file);
  fetch('/api/upload_bg', {method:'POST', body:fd})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.url) {
        bgUrl = d.url;
        localStorage.setItem('wb_bgUrl', bgUrl);
        pageStyle = 'bgimg';
        localStorage.setItem('wb_pageStyle', 'bgimg');
        applyStyles();
      } else { alert(d.error || '上传失败'); }
    })
    .catch(function(e){ alert('上传失败：' + e); });
});
function resetSettings(){
  localStorage.removeItem('wb_pageStyle'); localStorage.removeItem('wb_cardStyle');
  localStorage.removeItem('wb_pageStr'); localStorage.removeItem('wb_cardStr');
  localStorage.removeItem('wb_bgUrl'); localStorage.removeItem('wb_bgFit');
  localStorage.removeItem('wb_wrapW'); localStorage.removeItem('wb_fontS'); localStorage.removeItem('wb_fontF'); localStorage.removeItem('wb_fontCustom');
  localStorage.removeItem('wb_chartColor');
  pageStyle='default'; cardStyle='default'; pageStr=55; cardStr=70; bgUrl=''; bgFit='cover';
  wrapW=720; fontS=15; fontF='default'; chartColor='red';
  applyStyles();
}
function switchUser(){var u=document.getElementById('userSel').value;location.href='/?user='+u;}
/* 展开全部评论（懒加载，防抖避免重复请求） */
var _cmtLoading = null;
function expandComments(btn){
  var box = btn.parentNode.querySelector('.cmt-all');
  if (!box) return;
  if (box.style.display !== 'none') { box.style.display='none'; btn.innerHTML='展开全部 '+btn.dataset.total+' 条评论 ▾'; return; }
  if (btn.dataset.loaded) { box.style.display='block'; btn.innerHTML='收起评论 ▴'; return; }
  if (_cmtLoading) return;
  _cmtLoading = btn;
  btn.disabled = true;
  fetch('/api/comments?weibo_id=' + encodeURIComponent(btn.dataset.wid))
    .then(function(r){ return r.json(); })
    .then(function(arr){
      var html = '';
      arr.forEach(function(c){
        var ip = c.ip ? '<span class="cmt-ip">'+c.ip+'</span>' : '';
        var av = c.avatar ? '<img class="cmt-av" src="'+c.avatar+'" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">' : '<div class="cmt-av" style="display:none"></div>';
        html += '<div class="cmt"><img class="cmt-av" src="'+c.avatar+'" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">'
             + '<div class="cmt-body"><div class="cmt-hd"><b>'+esc(c.user)+'</b>'
             + '<span class="cmt-t">'+esc(c.time)+'</span>'+ip+'</div>'
             + '<div class="cmt-tx">'+esc(c.text)+'</div></div></div>';
      });
      box.innerHTML = html || '<div class="empty">暂无更多评论</div>';
      box.style.display = 'block';
      btn.dataset.loaded = '1';
      btn.innerHTML = '收起评论 ▴';
      btn.disabled = false;
      _cmtLoading = null;
    })
    .catch(function(e){ btn.disabled=false; _cmtLoading=null; alert('评论加载失败：' + e); });
}
function esc(s){ var d=document.createElement('div'); d.textContent=s||''; return d.innerHTML; }
buildOpts();
applyStyles();

/* ================= 灯箱 / 键盘翻页 / 已读续读 ================= */
(function () {
  function qs(name) {
    var m = new RegExp('[?&]' + name + '=([^&]*)').exec(location.search);
    return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : '';
  }
  function currentUid() {
    var sel = document.getElementById('userSel');
    return qs('user') || (sel ? sel.value : '');
  }
  var UID = currentUid();
  var LS_KEY = 'wb_last_' + UID;

  /* ---- 灯箱 ---- */
  var lb = null, lbImg = null, lbList = [], lbIdx = 0, lbInfo = null;

  function ensureLightbox() {
    if (lb) return lb;
    lb = document.createElement('div');
    lb.className = 'wb-lb';
    lb.innerHTML = '<div class="wb-lb-bar">' +
      '<span class="wb-lb-info"></span>' +
      '<span class="wb-lb-btns">' +
      '<button type="button" data-act="prev">‹</button>' +
      '<button type="button" data-act="next">›</button>' +
      '<button type="button" data-act="close">✕</button>' +
      '</span></div><img class="wb-lb-img" alt="">';
    document.body.appendChild(lb);
    lbImg = lb.querySelector('.wb-lb-img');
    lbInfo = lb.querySelector('.wb-lb-info');
    lb.addEventListener('click', function (e) {
      var act = e.target.getAttribute && e.target.getAttribute('data-act');
      if (act === 'prev') { step(-1); return; }
      if (act === 'next') { step(1); return; }
      if (act === 'close' || e.target === lb) closeLb();
    });
    return lb;
  }
  function showLb() {
    var src = lbList[lbIdx];
    lbImg.src = src;
    lbInfo.textContent = (lbIdx + 1) + ' / ' + lbList.length;
    lb.classList.add('on');
    document.body.classList.add('lb-open');
  }
  function step(d) {
    if (!lbList.length) return;
    lbIdx = (lbIdx + d + lbList.length) % lbList.length;
    showLb();
  }
  function closeLb() {
    if (!lb) return;
    lb.classList.remove('on');
    document.body.classList.remove('lb-open');
    lbImg.removeAttribute('src');
  }
  window.wbLightbox = function (img) {
    ensureLightbox();
    var box = img.closest('.pics') || img.parentNode;
    var all = [].slice.call(box.querySelectorAll('img'));
    lbList = all.map(function (i) { return i.currentSrc || i.src; });
    lbIdx = Math.max(0, all.indexOf(img));
    showLb();
  };

  /* ---- 键盘：← → 翻页，Esc 关灯箱 ---- */
  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    if (lb && lb.classList.contains('on')) {
      if (e.key === 'Escape') { closeLb(); e.preventDefault(); }
      else if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
      return;
    }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      var as = document.querySelectorAll('.pager a');
      if (!as.length) return;
      var a = e.key === 'ArrowLeft' ? as[0] : as[as.length - 1];
      if (a && a.style.pointerEvents !== 'none') { location.href = a.href; }
    }
  });

  /* ---- 已读标记 + 续读位置 ---- */
  var cards = [].slice.call(document.querySelectorAll('.card[data-ts]'));

  function visiblePos() {
    // 返回当前视口顶部第一条可见卡片的 data-ts
    for (var i = 0; i < cards.length; i++) {
      var r = cards[i].getBoundingClientRect();
      if (r.bottom > 60) return cards[i].getAttribute('data-ts');
    }
    return '';
  }
  function markRead() {
    for (var i = 0; i < cards.length; i++) {
      var r = cards[i].getBoundingClientRect();
      if (r.bottom < 0) cards[i].classList.add('read');
    }
  }
  var lastSave = 0;
  function onScroll() {
    var now = Date.now();
    if (now - lastSave < 800) return;
    lastSave = now;
    markRead();
    var ts = visiblePos();
    if (ts) { try { localStorage.setItem(LS_KEY, ts); } catch (e) {} }
  }
  if (cards.length) {
    window.addEventListener('scroll', onScroll, { passive: true });
    markRead();
  }

  /* ---- 续读提示条（只在时间线第 1 页显示）---- */
  function showResumeChip() {
    if (!UID) return;
    if (!/^\d+$/.test(qs('page') || '1') || (qs('page') || '1') !== '1') return;
    if (qs('view') || qs('fav') || qs('wid') || qs('q') || qs('d1') || qs('d2') || qs('to')) return;
    var ts = '';
    try { ts = localStorage.getItem(LS_KEY) || ''; } catch (e) {}
    if (!ts) return;
    if (cards.length && cards[0].getAttribute('data-ts') === ts) return; // 已经在最顶上
    var a = document.createElement('a');
    a.className = 'wb-resume';
    a.href = '/?user=' + encodeURIComponent(UID) + '&to=' + encodeURIComponent(ts);
    a.innerHTML = '⏱ 上次看到 <b>' + ts.slice(5, 16) + '</b> · 继续阅读';
    a.title = '跳到上次读到的位置';
    document.body.appendChild(a);
    setTimeout(function () { a.classList.add('out'); }, 12000);
  }
  showResumeChip();

  /* ---- ?hl=<ts> 定位并闪一下 ---- */
  var hl = qs('hl');
  if (hl) {
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].getAttribute('data-ts') === hl) {
        cards[i].classList.add('hl');
        cards[i].scrollIntoView({ block: 'center' });
        setTimeout(function (c) {
          return function () { c.classList.remove('hl'); };
        }(cards[i]), 2600);
        break;
      }
    }
  }
})();

/* ================= 自定义标签 ================= */
(function () {
  function post(wid, tag, act, cb) {
    var fd = new FormData();
    fd.append('wid', wid);
    fd.append('tag', tag);
    fd.append('act', act || 'add');
    fetch('/api/tag', { method: 'POST', body: fd })
      .then(function (r) { return r.json(); })
      .then(function (j) { cb(j && j.ok); })
      .catch(function () { cb(false); });
  }
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('.wb-tag') : null;
    if (!el) return;
    var wid = el.getAttribute('data-wid');
    if (el.classList.contains('add')) {
      e.preventDefault();
      var tag = prompt('给这条微博加个标签（例如：好吃的 / 仓鼠 / 面试）：');
      if (!tag) return;
      tag = tag.trim();
      if (!tag) return;
      post(wid, tag, 'add', function (ok) { if (ok) location.reload(); else alert('保存失败'); });
    } else if (e.shiftKey) {
      // Shift + 点击 = 删除这个标签
      e.preventDefault();
      var t = el.textContent.trim();
      if (!confirm('从这条微博上删除标签「' + t + '」？')) return;
      post(wid, t, 'del', function (ok) { if (ok) location.reload(); else alert('删除失败'); });
    }
  });
})();

/* ---- 图片加载失败：给占位，而不是缩成碎图标 ---- */
document.addEventListener('error', function (e) {
  var t = e.target;
  if (!t || t.tagName !== 'IMG') return;
  t.classList.add('img-broken');
  var ph = t.closest('.ph');
  if (ph) ph.classList.add('broken');
}, true);
