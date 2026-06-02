<script>
  import { onDestroy, onMount } from 'svelte'

  const filters = ['All', 'Politics', 'Crypto', 'Macro', 'Sports', 'Tech', 'Culture']
  const engines = ['All', 'CLOB', 'TWPM']
  const markets = [
    {
      title: 'Fed cuts by September 2026',
      category: 'Macro',
      engine: 'CLOB',
      volume: '$12.8M',
      yes: 0.61,
      no: 0.39,
      change: '+3.2%'
    },
    {
      title: 'Bitcoin above $100k this year',
      category: 'Crypto',
      engine: 'CLOB',
      volume: '$9.1M',
      yes: 0.58,
      no: 0.42,
      change: '-1.4%'
    },
    {
      title: 'AI regulation bill passes in 2026',
      category: 'Politics',
      engine: 'TWPM',
      volume: '$2.4M',
      yes: 0.47,
      no: 0.53,
      change: '+0.8%'
    },
    {
      title: 'Lakers reach conference finals',
      category: 'Sports',
      engine: 'TWPM',
      volume: '$1.9M',
      yes: 0.32,
      no: 0.68,
      change: '+2.1%'
    },
    {
      title: 'Top 5 streaming show in 2026 is sci-fi',
      category: 'Culture',
      engine: 'TWPM',
      volume: '$710k',
      yes: 0.44,
      no: 0.56,
      change: '-0.6%'
    },
    {
      title: 'Open-source model hits GPT-5 parity',
      category: 'Tech',
      engine: 'CLOB',
      volume: '$4.6M',
      yes: 0.29,
      no: 0.71,
      change: '+5.0%'
    }
  ]

  const activity = [
    'BUY 540 YES at 0.63 on Fed cuts',
    'SELL 210 NO at 0.44 on Bitcoin $100k',
    'BUY 120 YES at 0.41 on AI regulation bill',
    'BUY 90 YES at 0.31 on Lakers conference finals',
    'SELL 330 NO at 0.57 on sci-fi streaming leader',
    'BUY 760 YES at 0.28 on open-source parity'
  ]

  const orderbook = {
    bids: [
      ['0.62', '2,400'],
      ['0.61', '3,200'],
      ['0.60', '4,180'],
      ['0.59', '6,020']
    ],
    asks: [
      ['0.63', '1,900'],
      ['0.64', '2,700'],
      ['0.65', '3,100'],
      ['0.66', '5,440']
    ]
  }

  let activeFilter = 'All'
  let activeEngine = 'All'
  let isSearchOpen = false
  let buySell = 'buy'
  let orderType = 'market'
  let size = '250'
  let price = '0.62'
  let searchInput
  let overlayRef

  $: sizeValue = Number(size) || 0
  $: priceValue = Number(price) || 0
  $: notional = (sizeValue * priceValue).toFixed(2)
  $: fee = (sizeValue * priceValue * 0.015).toFixed(2)
  $: twpmPremium = orderType === 'pari' ? (sizeValue * 0.04).toFixed(2) : '0.00'

  const openSearch = () => {
    isSearchOpen = true
    setTimeout(() => {
      searchInput?.focus()
    }, 0)
  }

  const closeSearch = () => {
    isSearchOpen = false
  }

  const handleOverlayKeydown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      closeSearch()
    }
  }

  const handleKeydown = (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault()
      if (!isSearchOpen) {
        openSearch()
      }
      return
    }

    if (event.key === 'Escape' && isSearchOpen) {
      event.preventDefault()
      closeSearch()
      return
    }

    if (isSearchOpen && event.key === 'Tab') {
      const focusables = overlayRef?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (!focusables || focusables.length === 0) {
        return
      }
      const items = Array.from(focusables)
      const currentIndex = items.indexOf(document.activeElement)
      let nextIndex = currentIndex
      if (event.shiftKey) {
        nextIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1
      } else {
        nextIndex = currentIndex === items.length - 1 ? 0 : currentIndex + 1
      }
      event.preventDefault()
      items[nextIndex]?.focus()
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown)
    return () => window.removeEventListener('keydown', handleKeydown)
  })

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown)
  })

  $: if (typeof document !== 'undefined') {
    document.body.style.overflow = isSearchOpen ? 'hidden' : ''
  }
</script>

<div class="page">
  <header class="nav glass">
    <div class="brand">
      <span class="brand-mark"></span>
      Xpredict
    </div>
    <nav class="nav-links" aria-label="Primary">
      <a href="/" class="is-active">Markets</a>
      <a href="/">Portfolio</a>
      <a href="/">Insights</a>
      <a href="/">Liquidity</a>
    </nav>
    <div class="nav-actions">
      <button class="ghost" type="button" on:click={openSearch}>Search</button>
      <button class="cta" type="button">Create Market</button>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Liquidity first markets</p>
        <h1>Trade probability with speed and conviction.</h1>
        <p class="hero-sub">
          A hybrid prediction market built for depth. CLOB precision for top venues and
          TWPM pools that keep long-tail markets liquid from day one.
        </p>
        <div class="hero-actions">
          <button class="cta" type="button">Explore markets</button>
          <button class="ghost" type="button">View playbook</button>
        </div>
        <div class="hero-stats">
          <div class="stat glass">
            <span class="stat-label">24h volume</span>
            <span class="stat-value">$48.2M</span>
          </div>
          <div class="stat glass">
            <span class="stat-label">Open markets</span>
            <span class="stat-value">1,284</span>
          </div>
          <div class="stat glass">
            <span class="stat-label">Avg. spread</span>
            <span class="stat-value">0.012</span>
          </div>
        </div>
      </div>
      <div class="hero-spotlight glass">
        <div class="spotlight-top">
          <span class="pill">Featured</span>
          <span class="engine">CLOB</span>
        </div>
        <h2>Will the Fed cut rates before September 2026?</h2>
        <p class="spotlight-sub">Live order book with $12.8M depth and 820 active traders.</p>
        <div class="spotlight-prices">
          <button class="yes" type="button">Yes 61%</button>
          <button class="no" type="button">No 39%</button>
        </div>
        <div class="spotlight-footer">
          <span>Last trade 0.62</span>
          <span>1h change +3.2%</span>
        </div>
      </div>
    </section>

    <section class="filters glass">
      <div class="filter-row">
        {#each filters as filter}
          <button
            type="button"
            class:active={activeFilter === filter}
            class="pill"
            on:click={() => (activeFilter = filter)}
          >
            {filter}
          </button>
        {/each}
      </div>
      <div class="filter-row">
        {#each engines as engine}
          <button
            type="button"
            class:active={activeEngine === engine}
            class="pill outline"
            on:click={() => (activeEngine = engine)}
          >
            {engine}
          </button>
        {/each}
      </div>
    </section>

    <section class="market-grid">
      {#each markets as market, index}
        <article class="market-card glass" style={`animation-delay: ${index * 80}ms`}>
          <div class="card-top">
            <span class="pill small">{market.category}</span>
            <span class="engine">{market.engine}</span>
            <span class="volume">{market.volume}</span>
          </div>
          <h3>{market.title}</h3>
          <div class="sparkline">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="card-footer">
            <button class="yes" type="button">Yes {Math.round(market.yes * 100)}%</button>
            <button class="no" type="button">No {Math.round(market.no * 100)}%</button>
            <span class="change">{market.change}</span>
          </div>
        </article>
      {/each}
    </section>

    <section class="detail glass">
      <div class="detail-left">
        <div class="detail-header">
          <div>
            <p class="eyebrow">Market detail</p>
            <h2>Will the Fed cut rates before September 2026?</h2>
          </div>
          <div class="countdown">
            <span class="label">Resolves in</span>
            <span class="value">5d 12h</span>
          </div>
        </div>
        <div class="chart glass">
          <div class="chart-grid"></div>
          <div class="chart-line"></div>
          <div class="chart-overlay">
            <span>Mid 0.62</span>
            <span>24h range 0.56 - 0.66</span>
          </div>
        </div>
        <div class="orderbook glass">
          <div class="orderbook-header">
            <h3>Orderbook</h3>
            <span>Depth 6.4k shares</span>
          </div>
          <div class="orderbook-grid">
            <div>
              <div class="ob-title">Bids</div>
              {#each orderbook.bids as row}
                <div class="ob-row bid">
                  <span>{row[0]}</span>
                  <span>{row[1]}</span>
                </div>
              {/each}
            </div>
            <div>
              <div class="ob-title">Asks</div>
              {#each orderbook.asks as row}
                <div class="ob-row ask">
                  <span>{row[0]}</span>
                  <span>{row[1]}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
      <div class="detail-right">
        <div class="trade-terminal glass">
          <div class="terminal-header">
            <h3>Trade</h3>
            <span>Balance $12,480</span>
          </div>
          <div class="toggle">
            <button class:active={buySell === 'buy'} on:click={() => (buySell = 'buy')}
              >Buy</button
            >
            <button class:active={buySell === 'sell'} on:click={() => (buySell = 'sell')}
              >Sell</button
            >
          </div>
          <div class="tabs">
            <button class:active={orderType === 'market'} on:click={() => (orderType = 'market')}
              >Market</button
            >
            <button class:active={orderType === 'limit'} on:click={() => (orderType = 'limit')}
              >Limit</button
            >
            <button class:active={orderType === 'pari'} on:click={() => (orderType = 'pari')}
              >Pari-Mutuel</button
            >
          </div>
          <div class="field">
            <label for="size">Size</label>
            <input id="size" type="text" bind:value={size} />
          </div>
          {#if orderType !== 'market'}
            <div class="field">
              <label for="price">Limit price</label>
              <input id="price" type="text" bind:value={price} />
            </div>
          {/if}
          {#if orderType === 'pari'}
            <div class="field">
              <label for="weight">Time weight</label>
              <input id="weight" type="text" value="2.3x" readonly />
            </div>
          {/if}
          <div class="summary">
            <div>
              <span>Notional</span>
              <strong>${notional}</strong>
            </div>
            <div>
              <span>Fee</span>
              <strong>${fee}</strong>
            </div>
            <div>
              <span>TWPM premium</span>
              <strong>${twpmPremium}</strong>
            </div>
          </div>
          <button class="cta full" type="button">
            {buySell === 'buy' ? 'Place buy order' : 'Place sell order'}
          </button>
        </div>
      </div>
    </section>
  </main>

  <div class="ticker">
    <div class="ticker-track">
      {#each activity as item}
        <span>{item}</span>
      {/each}
      {#each activity as item}
        <span>{item}</span>
      {/each}
    </div>
  </div>
</div>

{#if isSearchOpen}
  <div
    class="overlay"
    role="button"
    tabindex="0"
    on:click|self={closeSearch}
    on:keydown={handleOverlayKeydown}
  >
    <div class="overlay-card glass" bind:this={overlayRef}>
      <div class="overlay-header">
        <h3>Search markets</h3>
        <button class="ghost" type="button" on:click={closeSearch}>Close</button>
      </div>
      <input
        bind:this={searchInput}
        type="text"
        placeholder="Search by market, ticker, or category"
        aria-label="Search markets"
      />
      <div class="overlay-results">
        <button type="button">
          <span class="result-title">Fed cuts by September 2026</span>
          <span class="result-meta">Macro · CLOB</span>
        </button>
        <button type="button">
          <span class="result-title">Bitcoin above $100k this year</span>
          <span class="result-meta">Crypto · CLOB</span>
        </button>
        <button type="button">
          <span class="result-title">AI regulation bill passes in 2026</span>
          <span class="result-meta">Politics · TWPM</span>
        </button>
      </div>
      <p class="overlay-hint">Tip: press Esc to close.</p>
    </div>
  </div>
{/if}
