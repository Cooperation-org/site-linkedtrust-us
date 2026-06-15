<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

  <xsl:output method="html"
              encoding="UTF-8"
              indent="yes"
              doctype-system="about:legacy-compat"/>

  <!-- ============================================================= -->
  <!-- Shared <head> with all branding/CSS inlined                   -->
  <!-- ============================================================= -->
  <xsl:template name="head">
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <meta name="robots" content="noindex, follow"/>
      <title>LinkedTrust XML Sitemap</title>
      <style type="text/css">
        :root {
          --cyan: #00B2E5;
          --purple: #667eea;
          --bg: #FAFAF8;
          --ink: #0f1117;
          --muted: #5b6470;
          --line: #e6e6e0;
        }
        * { box-sizing: border-box; }
        html { -webkit-text-size-adjust: 100%; }
        body {
          margin: 0;
          background: var(--bg);
          color: var(--ink);
          font-family: "Montserrat", -apple-system, BlinkMacSystemFont,
                       "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          line-height: 1.5;
          -webkit-font-smoothing: antialiased;
        }
        a { color: var(--purple); text-decoration: none; }
        a:hover { text-decoration: underline; }
        .mono {
          font-family: "JetBrains Mono", ui-monospace, SFMono-Regular,
                       Menlo, Consolas, monospace;
        }

        .hero {
          background: linear-gradient(120deg, var(--cyan) 0%, var(--purple) 100%);
          color: #fff;
          padding: 40px 24px;
        }
        .hero-inner { max-width: 1080px; margin: 0 auto; }
        .hero h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 800;
          letter-spacing: -0.01em;
        }
        .hero .note {
          margin: 8px 0 0;
          font-size: 14px;
          opacity: 0.92;
        }

        .wrap { max-width: 1080px; margin: 0 auto; padding: 28px 24px 64px; }

        .card {
          background: #fff;
          border: 1px solid var(--line);
          border-radius: 14px;
          overflow: hidden;
          box-shadow: 0 1px 2px rgba(15,17,23,0.04),
                      0 8px 24px rgba(15,17,23,0.05);
        }

        .meta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 16px 20px;
          border-bottom: 1px solid var(--line);
          flex-wrap: wrap;
        }
        .count {
          font-size: 13px;
          color: var(--muted);
        }
        .count strong { color: var(--ink); }
        .pill {
          display: inline-block;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          color: var(--purple);
          background: rgba(102,126,234,0.10);
          border-radius: 999px;
          padding: 4px 10px;
        }

        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        thead th {
          text-align: left;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          color: var(--muted);
          padding: 12px 20px;
          border-bottom: 1px solid var(--line);
          background: #fbfbf9;
        }
        tbody td {
          padding: 12px 20px;
          border-bottom: 1px solid var(--line);
          vertical-align: top;
        }
        tbody tr:nth-child(even) { background: #fafaf7; }
        tbody tr:hover { background: rgba(0,178,229,0.06); }
        tbody tr:last-child td { border-bottom: 0; }

        td.url a { word-break: break-all; }
        .num { font-variant-numeric: tabular-nums; color: var(--muted); white-space: nowrap; }

        .footer {
          max-width: 1080px;
          margin: 0 auto;
          padding: 0 24px 48px;
          font-size: 12px;
          color: var(--muted);
        }
        .footer a { color: var(--muted); text-decoration: underline; }

        @media (max-width: 560px) {
          .hero h1 { font-size: 22px; }
          thead th, tbody td { padding: 10px 12px; }
        }
      </style>
    </head>
  </xsl:template>

  <!-- ============================================================= -->
  <!-- Sitemap INDEX                                                  -->
  <!-- ============================================================= -->
  <xsl:template match="/s:sitemapindex">
    <html lang="en">
      <xsl:call-template name="head"/>
      <body>
        <div class="hero">
          <div class="hero-inner">
            <h1>LinkedTrust XML Sitemap</h1>
            <p class="note">This is an XML sitemap for search engines.</p>
          </div>
        </div>
        <div class="wrap">
          <div class="card">
            <div class="meta">
              <span class="pill">Sitemap Index</span>
              <span class="count">
                This index contains
                <strong><xsl:value-of select="count(s:sitemap)"/></strong>
                sitemaps.
              </span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Sitemap</th>
                  <th>Last Modified</th>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="s:sitemap">
                  <tr>
                    <td class="url">
                      <a class="mono" href="{s:loc}">
                        <xsl:value-of select="s:loc"/>
                      </a>
                    </td>
                    <td class="num">
                      <xsl:choose>
                        <xsl:when test="s:lastmod">
                          <xsl:value-of select="s:lastmod"/>
                        </xsl:when>
                        <xsl:otherwise>&#8212;</xsl:otherwise>
                      </xsl:choose>
                    </td>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>
        </div>
        <div class="footer">
          Generated by <a href="https://linkedtrust.us">LinkedTrust</a>.
        </div>
      </body>
    </html>
  </xsl:template>

  <!-- ============================================================= -->
  <!-- URL SET                                                        -->
  <!-- ============================================================= -->
  <xsl:template match="/s:urlset">
    <html lang="en">
      <xsl:call-template name="head"/>
      <body>
        <div class="hero">
          <div class="hero-inner">
            <h1>LinkedTrust XML Sitemap</h1>
            <p class="note">This is an XML sitemap for search engines.</p>
          </div>
        </div>
        <div class="wrap">
          <div class="card">
            <div class="meta">
              <span class="pill">URL Set</span>
              <span class="count">
                This sitemap contains
                <strong><xsl:value-of select="count(s:url)"/></strong>
                URLs.
              </span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>URL</th>
                  <xsl:if test="s:url/s:priority">
                    <th>Priority</th>
                  </xsl:if>
                  <xsl:if test="s:url/s:changefreq">
                    <th>Change Freq.</th>
                  </xsl:if>
                  <xsl:if test="s:url/s:lastmod">
                    <th>Last Modified</th>
                  </xsl:if>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="s:url">
                  <tr>
                    <td class="url">
                      <a class="mono" href="{s:loc}">
                        <xsl:value-of select="s:loc"/>
                      </a>
                    </td>
                    <xsl:if test="/s:urlset/s:url/s:priority">
                      <td class="num">
                        <xsl:choose>
                          <xsl:when test="s:priority">
                            <xsl:value-of select="s:priority"/>
                          </xsl:when>
                          <xsl:otherwise>&#8212;</xsl:otherwise>
                        </xsl:choose>
                      </td>
                    </xsl:if>
                    <xsl:if test="/s:urlset/s:url/s:changefreq">
                      <td class="num">
                        <xsl:choose>
                          <xsl:when test="s:changefreq">
                            <xsl:value-of select="s:changefreq"/>
                          </xsl:when>
                          <xsl:otherwise>&#8212;</xsl:otherwise>
                        </xsl:choose>
                      </td>
                    </xsl:if>
                    <xsl:if test="/s:urlset/s:url/s:lastmod">
                      <td class="num">
                        <xsl:choose>
                          <xsl:when test="s:lastmod">
                            <xsl:value-of select="s:lastmod"/>
                          </xsl:when>
                          <xsl:otherwise>&#8212;</xsl:otherwise>
                        </xsl:choose>
                      </td>
                    </xsl:if>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>
        </div>
        <div class="footer">
          Generated by <a href="https://linkedtrust.us">LinkedTrust</a>.
        </div>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>
