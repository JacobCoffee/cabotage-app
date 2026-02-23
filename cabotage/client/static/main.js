/* ===== Cabotage PaaS - Vanilla JS ===== */

/* ---------- Slugify ---------- */
function slugify(text) {
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '')
    .replace(/[\s_-]+/g, '-');
}

function applySlugify(sourceSelector, destinationSelector) {
  var dest = document.querySelector(destinationSelector);
  var source = document.querySelector(sourceSelector);
  if (!dest || !source) return;
  dest.addEventListener('keyup', function () {
    if (!dest.classList.contains('user-has-edited')) {
      dest.classList.add('user-has-edited');
    }
  });
  source.addEventListener('keyup', function () {
    if (!dest.classList.contains('user-has-edited')) {
      dest.value = slugify(source.value);
    }
  });
}

/* ---------- Tab Navigation ---------- */
function initTabs(containerSelector) {
  var container = document.querySelector(containerSelector || '[data-tabs]');
  if (!container) return;

  var tabs = container.querySelectorAll('[data-tab]');
  var panels = document.querySelectorAll('[data-tab-panel]');

  function activateTab(tabId) {
    tabs.forEach(function(t) {
      t.classList.toggle('tab-active', t.getAttribute('data-tab') === tabId);
    });

    // Emit lifecycle events before toggling visibility
    panels.forEach(function(p) {
      var panelId = p.getAttribute('data-tab-panel');
      if (panelId === tabId) {
        p.classList.add('tab-panel-active');
        p.dispatchEvent(new CustomEvent('tab-activated'));
      } else if (p.classList.contains('tab-panel-active')) {
        p.dispatchEvent(new CustomEvent('tab-deactivated'));
        p.classList.remove('tab-panel-active');
      }
    });

    // Update URL hash without scrolling
    if (history.replaceState) {
      history.replaceState(null, null, '#' + tabId);
    }
  }

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function(e) {
      e.preventDefault();
      activateTab(tab.getAttribute('data-tab'));
    });
  });

  // Activate from URL hash or default to first tab
  var hash = window.location.hash.replace('#', '');
  var validTab = false;
  tabs.forEach(function(t) {
    if (t.getAttribute('data-tab') === hash) validTab = true;
  });

  if (validTab) {
    activateTab(hash);
  } else if (tabs.length > 0) {
    activateTab(tabs[0].getAttribute('data-tab'));
  }
}

/* ---------- Increment/Decrement (Process Scaling) ---------- */
function initCountInputs() {
  document.querySelectorAll('.incr-btn').forEach(function(button) {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      var parent = button.closest('.count-input');
      if (!parent) return;
      var input = parent.querySelector('.quantity');
      if (!input) return;

      var oldValue = parseFloat(input.value) || 0;
      var decrBtn = parent.querySelector('.incr-btn[data-action="decrease"]');
      if (decrBtn) decrBtn.classList.remove('inactive');

      if (button.getAttribute('data-action') === 'increase') {
        input.value = oldValue + 1;
      } else {
        input.value = Math.max(0, oldValue - 1);
        if (input.value == 0 && decrBtn) decrBtn.classList.add('inactive');
      }

      // Show the update button
      document.querySelectorAll('.update_process_settings').forEach(function(el) {
        el.classList.remove('hidden');
      });
    });
  });

  // Pod size change handler
  document.querySelectorAll('.pod-size').forEach(function(select) {
    select.addEventListener('change', function() {
      document.querySelectorAll('.update_process_settings').forEach(function(el) {
        el.classList.remove('hidden');
      });
    });
  });
}

/* ---------- Env Var Reveal ---------- */
function initEnvReveal() {
  document.querySelectorAll('[data-reveal]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = document.getElementById(btn.getAttribute('data-reveal'));
      if (!target) return;
      var hidden = target.querySelector('.env-hidden');
      var shown = target.querySelector('.env-shown');
      if (hidden && shown) {
        hidden.classList.toggle('hidden');
        shown.classList.toggle('hidden');
        btn.textContent = hidden.classList.contains('hidden') ? 'Hide' : 'Reveal';
      }
    });
  });
}

/* ---------- Dropdown Close ---------- */
function initDropdowns() {
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
      document.querySelectorAll('.dropdown [tabindex]').forEach(function(el) {
        el.blur();
      });
    }
  });
}

/* ---------- Mobile Nav Toggle ---------- */
function initMobileNav() {
  var toggle = document.getElementById('mobile-nav-toggle');
  var menu = document.getElementById('mobile-nav-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function() {
      menu.classList.toggle('hidden');
    });
  }
}

/* ---------- Theme Toggle (3-state: light → dark → system) ---------- */
function initThemeToggle() {
  function resolveSystem() {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function applyPref(pref) {
    var resolved = pref === 'system' ? resolveSystem() : pref;
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-pref', pref);
    localStorage.setItem('theme-pref', pref);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.content = resolved === 'light' ? '#fafafe' : '#0f0f17';
    }
  }

  function cyclePref() {
    var current = localStorage.getItem('theme-pref') || 'system';
    var next = current === 'light' ? 'dark' : current === 'dark' ? 'system' : 'light';
    applyPref(next);
  }

  // Bind all toggle buttons
  document.querySelectorAll('#theme-toggle, #theme-toggle-unauth').forEach(function(btn) {
    btn.addEventListener('click', cyclePref);
  });

  // Listen for system theme changes (update resolved theme when in system mode)
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function() {
    var pref = localStorage.getItem('theme-pref') || 'system';
    if (pref === 'system') {
      applyPref('system');
    }
  });

  // Ensure data-theme-pref attribute is set on load
  var pref = localStorage.getItem('theme-pref') || 'system';
  document.documentElement.setAttribute('data-theme-pref', pref);
}

/* ---------- Raw Editor Modal ---------- */
function initRawEditor() {
  var modal = document.getElementById('raw-editor-modal');
  if (!modal) return;

  var openBtn = document.getElementById('raw-editor-open');
  var closeBtn = document.getElementById('raw-editor-close');
  var cancelBtn = document.getElementById('raw-editor-cancel');
  var backdrop = modal.querySelector('.raw-editor-backdrop');
  var textarea = document.getElementById('raw-editor-textarea');
  var formatInput = document.getElementById('raw-editor-format');
  var copyBtn = document.getElementById('raw-editor-copy');
  var tabs = modal.querySelectorAll('[data-editor-tab]');
  var panels = modal.querySelectorAll('[data-editor-panel]');

  function openModal() {
    modal.style.display = 'flex';
    if (textarea) textarea.focus();
  }
  function closeModal() {
    modal.style.display = 'none';
  }

  if (openBtn) openBtn.addEventListener('click', openModal);
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
  if (backdrop) backdrop.addEventListener('click', closeModal);

  // Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.style.display !== 'none') {
      closeModal();
    }
  });

  // Tab switching
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      var tabId = tab.getAttribute('data-editor-tab');
      tabs.forEach(function(t) {
        t.classList.toggle('raw-editor-tab-active', t.getAttribute('data-editor-tab') === tabId);
      });
      panels.forEach(function(p) {
        p.style.display = p.getAttribute('data-editor-panel') === tabId ? '' : 'none';
      });
      if (formatInput) formatInput.value = tabId;

      // Update placeholder
      if (textarea) {
        if (tabId === 'json') {
          textarea.placeholder = '{\n  "DATABASE_URL": "postgres://...",\n  "REDIS_URL": "redis://..."\n}';
        } else {
          textarea.placeholder = '# Paste your environment variables here\nDATABASE_URL=postgres://...\nREDIS_URL=redis://...';
        }
      }
    });
  });

  // Copy ENV button
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      var dataEl = document.getElementById('env-export-data');
      if (!dataEl) return;
      try {
        var configs = JSON.parse(dataEl.textContent);
        var lines = configs.map(function(c) {
          if (c.secret) return c.name + '=**secure**';
          return c.name + '=' + c.value;
        });
        var text = lines.join('\n');
        navigator.clipboard.writeText(text).then(function() {
          var orig = copyBtn.innerHTML;
          copyBtn.textContent = 'Copied!';
          setTimeout(function() { copyBtn.innerHTML = orig; }, 1500);
        });
      } catch (e) {
        // ignore
      }
    });
  }
}

/* ---------- Add Variable Modal ---------- */
function initAddVarModal() {
  var modal = document.getElementById('add-var-modal');
  if (!modal) return;

  function openModal() {
    modal.style.display = 'flex';
    var nameInput = modal.querySelector('input[name="name"]');
    if (nameInput) { nameInput.value = ''; nameInput.focus(); }
    var valueInput = modal.querySelector('input[name="value"]');
    if (valueInput) valueInput.value = '';
  }
  function closeModal() {
    modal.style.display = 'none';
  }

  // Open buttons
  document.querySelectorAll('#add-var-open, [data-add-var-open]').forEach(function(btn) {
    btn.addEventListener('click', openModal);
  });

  // Close buttons/backdrop
  modal.querySelectorAll('[data-add-var-close]').forEach(function(el) {
    el.addEventListener('click', closeModal);
  });

  // Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.style.display !== 'none') {
      closeModal();
    }
  });

  // Auto-uppercase name field
  var nameField = modal.querySelector('input[name="name"]');
  if (nameField) {
    nameField.addEventListener('input', function() {
      var pos = this.selectionStart;
      this.value = this.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
      this.selectionStart = this.selectionEnd = pos;
    });
  }
}

/* ---------- Expand Modal ---------- */
function initExpandModal() {
  var modal = document.getElementById('expand-modal');
  if (!modal) return;

  var titleEl = modal.querySelector('.expand-modal-title');
  var bodyEl = modal.querySelector('.expand-modal-body');
  var copyBtn = modal.querySelector('.expand-modal-copy');
  var closeBtn = modal.querySelector('.expand-modal-close');
  var backdrop = modal.querySelector('.raw-editor-backdrop');

  function openModal(title, content) {
    titleEl.textContent = title;
    bodyEl.innerHTML = content;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (backdrop) backdrop.addEventListener('click', closeModal);

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closeModal();
    }
  });

  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      var text = bodyEl.textContent;
      navigator.clipboard.writeText(text).then(function() {
        var orig = copyBtn.innerHTML;
        copyBtn.textContent = 'Copied!';
        setTimeout(function() { copyBtn.innerHTML = orig; }, 1500);
      });
    });
  }

  // Bind all expand buttons
  document.querySelectorAll('[data-expand]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var targetId = btn.getAttribute('data-expand');
      var target = document.getElementById(targetId);
      if (!target) return;
      var title = btn.getAttribute('data-expand-title') || 'Details';
      openModal(title, target.innerHTML);
    });
  });
}

/* ---------- Detail Log Height Sync ---------- */
function getColumnNaturalHeight(col) {
  var children = col.children;
  var gap = parseFloat(getComputedStyle(col).rowGap) || 16;
  var h = 0;
  for (var i = 0; i < children.length; i++) {
    h += children[i].offsetHeight;
  }
  h += gap * Math.max(0, children.length - 1);
  return h;
}

function autoExpandCollapsibleCards() {
  var left = document.querySelector('[data-log-left]');
  var logCol = document.getElementById('log-column');
  if (!left || !logCol) return;
  if (window.innerWidth < 1024) return;

  var cards = left.querySelectorAll('details[data-collapsible-card]');
  if (!cards.length) return;

  /* Measure right column natural height (sum of children) */
  var logHeight = getColumnNaturalHeight(logCol);

  /* Open left-column cards one by one while left is shorter than right */
  for (var i = 0; i < cards.length; i++) {
    if (getColumnNaturalHeight(left) >= logHeight) break;
    cards[i].open = true;
  }
}

function syncDetailLogHeight() {
  var left = document.querySelector('[data-log-left]');
  var logViewer = document.querySelector('[data-log-viewer]');
  if (!left || !logViewer) return;
  if (window.innerWidth < 1024) {
    logViewer.style.maxHeight = '';
    return;
  }
  var naturalH = getColumnNaturalHeight(left);
  var minH = window.innerHeight * 0.7;
  var cardPad = 32; /* card-body !p-4 top+bottom */
  var headerH = 48; /* log header row approx */
  var h = Math.max(naturalH, minH) - cardPad - headerH;
  logViewer.style.maxHeight = Math.max(h, 200) + 'px';
}

/* ---------- Build Progress Tracker ---------- */
function BuildProgressTracker(barFill, phaseLabel, type) {
  this.barFill = barFill;
  this.phaseLabel = phaseLabel;
  this.type = type || 'build'; // 'build' or 'deploy'
  this.progress = 0;
  this.maxStep = 0;
  this.totalSteps = 0;
  this.activated = false;

  // Deploy phase definitions with cumulative progress targets
  this.deployPhases = [
    { pattern: /Constructing API Clients/i, label: 'Constructing API clients', progress: 5 },
    { pattern: /Fetching Namespace/i, label: 'Fetching namespace', progress: 10 },
    { pattern: /Fetching ServiceAccount/i, label: 'Fetching service account', progress: 15 },
    { pattern: /Fetching CabotageEnrollment/i, label: 'Fetching enrollment', progress: 20 },
    { pattern: /Fetching ImagePullSecrets/i, label: 'Fetching pull secrets', progress: 30 },
    { pattern: /Patching ServiceAccount/i, label: 'Patching service account', progress: 35 },
    { pattern: /Running release command/i, label: 'Running release command', progress: 45 },
    { pattern: /Creating deployment for/i, label: 'Creating deployment', progress: 55 },
    { pattern: /Creating Service for/i, label: 'Creating services', progress: 60 },
    { pattern: /Waiting on deployment to rollout/i, label: 'Waiting for rollout', progress: 70 },
    { pattern: /Running postdeploy/i, label: 'Running postdeploy', progress: 85 },
    { pattern: /Deployment .* complete/i, label: 'Deployment complete', progress: 100 },
  ];
}

BuildProgressTracker.prototype.activate = function() {
  if (this.activated) return;
  this.activated = true;
  this.barFill.classList.add('build-progress-bar-determinate');
  this.barFill.style.width = '0%';
};

BuildProgressTracker.prototype.setProgress = function(pct) {
  // Never go backwards
  if (pct <= this.progress) return;
  this.progress = pct;
  this.barFill.style.width = Math.min(pct, 100) + '%';
};

BuildProgressTracker.prototype.setPhase = function(text) {
  if (this.phaseLabel) {
    this.phaseLabel.textContent = text;
  }
};

BuildProgressTracker.prototype.processLine = function(line) {
  if (this.type === 'deploy') {
    this.processDeployLine(line);
  } else {
    this.processBuildLine(line);
  }
};

BuildProgressTracker.prototype.processBuildLine = function(line) {
  // Detect [M/N] step pattern from BuildKit
  var stepMatch = line.match(/\[(\d+)\/(\d+)\]/);
  if (stepMatch) {
    this.activate();
    var current = parseInt(stepMatch[1], 10);
    var total = parseInt(stepMatch[2], 10);
    if (total > this.totalSteps) this.totalSteps = total;
    if (current > this.maxStep) this.maxStep = current;
    // Steps occupy 5-75% range
    var pct = 5 + (this.maxStep / this.totalSteps) * 70;
    this.setProgress(pct);
    this.setPhase('Building step ' + this.maxStep + '/' + this.totalSteps);
    return;
  }

  // Detect exporting phase
  if (/exporting to image/i.test(line)) {
    this.activate();
    this.setProgress(78);
    this.setPhase('Exporting image');
    return;
  }

  // Detect pushing phase
  if (/pushing manifest/i.test(line) || /pushing layers/i.test(line)) {
    this.activate();
    this.setProgress(90);
    this.setPhase('Pushing image');
    return;
  }

  // Detect early setup phases (activate bar but low progress)
  if (/load build definition/i.test(line) || /resolve image config/i.test(line)) {
    this.activate();
    this.setProgress(2);
    this.setPhase('Resolving build');
    return;
  }
};

BuildProgressTracker.prototype.processDeployLine = function(line) {
  for (var i = 0; i < this.deployPhases.length; i++) {
    if (this.deployPhases[i].pattern.test(line)) {
      this.activate();
      this.setProgress(this.deployPhases[i].progress);
      this.setPhase(this.deployPhases[i].label);
      return;
    }
  }

  // Activate on any log line if not yet activated
  if (!this.activated && line.trim().length > 0) {
    this.activate();
    this.setProgress(2);
    this.setPhase('Starting deployment');
  }
};

BuildProgressTracker.prototype.complete = function() {
  this.activate();
  this.setProgress(100);
  this.setPhase('Complete');
};

/* ---------- Init All ---------- */
document.addEventListener('DOMContentLoaded', function() {
  initTabs();
  initCountInputs();
  initEnvReveal();
  initDropdowns();
  initMobileNav();
  initThemeToggle();
  initRawEditor();
  initAddVarModal();
  initExpandModal();
  autoExpandCollapsibleCards();
  syncDetailLogHeight();
  window.addEventListener('resize', function() {
    autoExpandCollapsibleCards();
    syncDetailLogHeight();
  });
});
