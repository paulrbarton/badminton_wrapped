/**
 * Badminton Wrapped - Awards Website
 * Vanilla JS SPA with hash-based routing.
 *
 * Routes:
 *   #/                         — Season selector (homepage)
 *   #/{season}                 — Club grid for a season
 *   #/{season}/{club-slug}     — Award cards for a club
 */

(function () {
    "use strict";

    const app = document.getElementById("app");

    // Data cache: { "2024-25": { season, clubs } }
    const cache = {};
    let seasons = null;

    // ── Helpers ──────────────────────────────────────────

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`Failed to fetch ${url}: ${resp.status}`);
        return resp.json();
    }

    async function getSeasons() {
        if (!seasons) {
            seasons = await fetchJSON("data/seasons.json");
        }
        return seasons;
    }

    async function getSeasonData(season) {
        if (!cache[season]) {
            cache[season] = await fetchJSON(`data/${season}.json`);
        }
        return cache[season];
    }

    /**
     * Parse pipe-delimited award_details into an array of strings.
     */
    function parseDetails(details) {
        if (!details) return [];
        return details
            .split(" | ")
            .map((d) => d.trim())
            .filter(Boolean);
    }

    /**
     * Sort awards by the configured display order.
     */
    function sortAwards(awards) {
        return [...awards].sort((a, b) => {
            const ai = AWARD_ORDER.indexOf(a.award);
            const bi = AWARD_ORDER.indexOf(b.award);
            // Unknown awards go to the end
            return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
        });
    }

    // ── Render Functions ────────────────────────────────

    function renderHeader() {
        return `
            <header class="site-header">
                <h1 class="site-title">🏸 Badminton <span class="accent">Wrapped</span></h1>
                <p class="site-subtitle">Nottinghamshire Badminton League Awards</p>
            </header>
        `;
    }

    function renderBreadcrumbs(items) {
        // items: [ { label, hash }, ... ] — last item has no hash (current page)
        const parts = items.map((item, i) => {
            if (i === items.length - 1) {
                return `<span class="current">${escapeHtml(item.label)}</span>`;
            }
            return `<a href="${item.hash}">${escapeHtml(item.label)}</a>`;
        });
        return `<nav class="breadcrumbs">${parts.join('<span class="separator">›</span>')}</nav>`;
    }

    function renderNetDecoration() {
        return '<div class="net-decoration"></div>';
    }

    // ── Season Page (Homepage) ──────────────────────────

    async function renderSeasonsPage() {
        try {
            const seasonList = await getSeasons();

            // Pre-fetch all season data to show club counts
            const seasonMeta = await Promise.all(
                seasonList.map(async (s) => {
                    try {
                        const data = await getSeasonData(s);
                        const clubCount = Object.keys(data.clubs).length;
                        const awardCount = Object.values(data.clubs).reduce(
                            (sum, c) => sum + c.awards.length,
                            0
                        );
                        return { season: s, clubCount, awardCount };
                    } catch {
                        return { season: s, clubCount: 0, awardCount: 0 };
                    }
                })
            );

            const cards = seasonMeta
                .map(
                    (m) => `
                <div class="season-card" onclick="location.hash='/${m.season}'" role="button" tabindex="0">
                    <div class="season-icon">🏸</div>
                    <div class="season-name">${escapeHtml(m.season)}</div>
                    <div class="season-meta">
                        ${m.clubCount} clubs · ${m.awardCount} awards
                    </div>
                </div>
            `
                )
                .join("");

            app.innerHTML = `
                <div class="fade-in">
                    ${renderHeader()}
                    ${renderNetDecoration()}
                    <section class="section-header">
                        <h2>Select a Season</h2>
                    </section>
                    <div class="season-grid">${cards}</div>
                    <footer class="site-footer">
                        Nottinghamshire Badminton League · Data from league match results
                    </footer>
                </div>
            `;

            // Keyboard support for season cards
            app.querySelectorAll(".season-card").forEach((card) => {
                card.addEventListener("keydown", (e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        card.click();
                    }
                });
            });
        } catch (err) {
            app.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <p>Failed to load seasons. Check that data files exist.</p>
                </div>
            `;
            console.error(err);
        }
    }

    // ── Club Grid Page ──────────────────────────────────

    async function renderClubsPage(season) {
        try {
            const data = await getSeasonData(season);
            const clubs = Object.entries(data.clubs).sort((a, b) =>
                a[1].name.localeCompare(b[1].name)
            );

            if (clubs.length === 0) {
                app.innerHTML = `
                    <div class="fade-in">
                        ${renderHeader()}
                        ${renderBreadcrumbs([
                            { label: "Home", hash: "#/" },
                            { label: season },
                        ])}
                        <div class="empty-state">
                            <div class="empty-icon">📭</div>
                            <p>No award data for the ${escapeHtml(season)} season yet.</p>
                            <p style="margin-top:0.5rem"><a href="#/">← Back to seasons</a></p>
                        </div>
                    </div>
                `;
                return;
            }

            const cards = clubs
                .map(
                    ([slug, club]) => `
                <div class="club-card" onclick="location.hash='/${season}/${slug}'" role="button" tabindex="0">
                    <div class="club-icon">🏸</div>
                    <div class="club-info">
                        <div class="club-name">${escapeHtml(club.name)}</div>
                        <div class="club-meta">${club.awards.length} award${club.awards.length !== 1 ? "s" : ""}</div>
                    </div>
                    <div class="club-arrow">›</div>
                </div>
            `
                )
                .join("");

            app.innerHTML = `
                <div class="fade-in">
                    ${renderHeader()}
                    ${renderBreadcrumbs([
                        { label: "Home", hash: "#/" },
                        { label: season },
                    ])}
                    ${renderNetDecoration()}
                    <section class="section-header">
                        <h2>${escapeHtml(season)} Season</h2>
                        <span class="badge">${clubs.length} clubs</span>
                    </section>
                    <div class="club-grid">${cards}</div>
                    <footer class="site-footer">
                        Nottinghamshire Badminton League · Data from league match results
                    </footer>
                </div>
            `;

            // Keyboard support
            app.querySelectorAll(".club-card").forEach((card) => {
                card.addEventListener("keydown", (e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        card.click();
                    }
                });
            });
        } catch (err) {
            app.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <p>Could not load data for season ${escapeHtml(season)}.</p>
                    <p style="margin-top:0.5rem"><a href="#/">← Back to seasons</a></p>
                </div>
            `;
            console.error(err);
        }
    }

    // ── Club Awards Page ────────────────────────────────

    function renderAwardCard(award) {
        const config = getAwardConfig(award.award);
        const details = parseDetails(award.award_details);
        const previewCount = 3;
        const hasMore = details.length > previewCount;

        let playerDisplay = escapeHtml(award.player);
        if (award.player_2) {
            playerDisplay += ` <span style="color:var(--accent)">&amp;</span> ${escapeHtml(award.player_2)}`;
        }

        const detailItems = details
            .slice(0, previewCount)
            .map((d) => `<li class="award-detail-item">${escapeHtml(d)}</li>`)
            .join("");

        const hiddenItems = details
            .slice(previewCount)
            .map((d) => `<li class="award-detail-item">${escapeHtml(d)}</li>`)
            .join("");

        const detailsId = `details-${award.award}-${award.player.replace(/\s+/g, "-").toLowerCase()}`;

        return `
            <div class="award-card" data-award="${award.award}">
                <div class="award-card-header" onclick="this.parentElement.classList.toggle('expanded')">
                    <div class="award-card-top">
                        <div class="award-emoji">${config.emoji}</div>
                        <div class="award-info">
                            <div class="award-type">${escapeHtml(config.isPartnership ? "Partnership Award" : "Individual Award")}</div>
                            <div class="award-title">${escapeHtml(config.title)}</div>
                        </div>
                    </div>
                    <div class="award-player">
                        <span class="award-player-name">${playerDisplay}</span>
                    </div>
                    <div class="award-value-row">
                        <span class="award-value">${escapeHtml(String(Math.round(award.award_value)))}</span>
                        <span class="award-value-unit">${escapeHtml(config.unit)}</span>
                    </div>
                    <div class="award-toggle">
                        <span>Details</span>
                        <span class="award-toggle-icon">▾</span>
                    </div>
                </div>
                <div class="award-details">
                    <div class="award-details-inner">
                        <p class="award-description">${escapeHtml(config.description)}</p>
                        <ul class="award-detail-list" id="${detailsId}">
                            ${detailItems}
                        </ul>
                        ${hasMore ? `
                            <ul class="award-detail-list" id="${detailsId}-hidden" style="display:none">
                                ${hiddenItems}
                            </ul>
                            <button class="show-more-btn" onclick="event.stopPropagation(); toggleMore(this, '${detailsId}-hidden', ${details.length - previewCount})">
                                Show ${details.length - previewCount} more…
                            </button>
                        ` : ""}
                    </div>
                </div>
            </div>
        `;
    }

    // Global toggle function for "show more" button
    window.toggleMore = function (btn, hiddenId, count) {
        const hidden = document.getElementById(hiddenId);
        if (!hidden) return;
        if (hidden.style.display === "none") {
            hidden.style.display = "";
            btn.textContent = "Show less";
        } else {
            hidden.style.display = "none";
            btn.textContent = `Show ${count} more…`;
        }
    };

    async function renderAwardsPage(season, clubSlug) {
        try {
            const data = await getSeasonData(season);
            const club = data.clubs[clubSlug];

            if (!club) {
                app.innerHTML = `
                    <div class="fade-in">
                        ${renderHeader()}
                        ${renderBreadcrumbs([
                            { label: "Home", hash: "#/" },
                            { label: season, hash: `#/${season}` },
                            { label: "Not Found" },
                        ])}
                        <div class="empty-state">
                            <div class="empty-icon">🔍</div>
                            <p>Club not found.</p>
                            <p style="margin-top:0.5rem"><a href="#/${season}">← Back to clubs</a></p>
                        </div>
                    </div>
                `;
                return;
            }

            const sortedAwards = sortAwards(club.awards);
            const awardCards = sortedAwards.map(renderAwardCard).join("");

            app.innerHTML = `
                <div class="fade-in">
                    ${renderHeader()}
                    ${renderBreadcrumbs([
                        { label: "Home", hash: "#/" },
                        { label: season, hash: `#/${season}` },
                        { label: club.name },
                    ])}
                    ${renderNetDecoration()}
                    <section class="section-header">
                        <h2>${escapeHtml(club.name)}</h2>
                        <span class="badge">${escapeHtml(season)} season · ${club.awards.length} awards</span>
                    </section>
                    <div class="award-grid">${awardCards}</div>
                    <footer class="site-footer">
                        Nottinghamshire Badminton League · Data from league match results
                    </footer>
                </div>
            `;
        } catch (err) {
            app.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <p>Could not load awards data.</p>
                    <p style="margin-top:0.5rem"><a href="#/${season}">← Back to clubs</a></p>
                </div>
            `;
            console.error(err);
        }
    }

    // ── Router ──────────────────────────────────────────

    async function route() {
        const hash = location.hash.replace(/^#\/?/, "");
        const parts = hash.split("/").filter(Boolean);

        if (parts.length === 0) {
            await renderSeasonsPage();
        } else if (parts.length === 1) {
            await renderClubsPage(parts[0]);
        } else if (parts.length === 2) {
            await renderAwardsPage(parts[0], parts[1]);
        } else {
            // Unknown route → go home
            location.hash = "#/";
        }

        // Scroll to top on navigation
        window.scrollTo(0, 0);
    }

    // ── Init ────────────────────────────────────────────

    window.addEventListener("hashchange", route);

    // Handle initial load
    if (!location.hash || location.hash === "#" || location.hash === "#/") {
        location.hash = "#/";
    }
    route();
})();
