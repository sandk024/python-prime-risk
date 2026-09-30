// Unit tests for the tangible Rewards system (public/streak.js) with simulated local dates. Run: node scripts/test-rewards.mjs
import * as S from "../public/streak.js";
let pass = 0, fail = 0;
const t = (name, fn) => { try { fn(); pass++; console.log("ok  ", name); } catch (e) { fail++; console.log("FAIL", name, "→", e.message); } };
const eq = (a, b, m = "") => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${m} expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`); };
const day = (n) => S.addDays("2026-10-01", n);
const study = (g, d) => { S.reconcile(g, d); return S.recordActivity(g, d, "lesson"); };
const run = (g, from, n) => { const ev = []; for (let i = 0; i < n; i++) ev.push(...study(g, day(from + i)).map(e => ({ ...e, on: day(from + i) }))); return ev.filter(e => e.type === "reward"); };

t("defaults: 4 rewards at 7/30/60/100 with Jacob's items", () => {
  const g = S.newGame(); eq(g.rewards.items.map(r => r.days), [7, 30, 60, 100]);
  eq(g.rewards.items.map(r => r.name), ["Race nutrition box (gels/chews)", "New pair of trail running shoes", "Race entry of your choice", "GPS watch or hydration vest upgrade"]);
  if (!g.rewards.items[2].note.includes("Black Canyon 100k (Feb 13, 2027)")) throw new Error("60-day note");
});
t("day 6 locked; day 7 unlocks the 7-day reward exactly once, dated that day", () => {
  const g = S.newGame(); eq(run(g, 0, 6).length, 0); eq(S.rewardState(g, "r7"), "locked");
  eq(S.nextReward(g, day(6)).toGo, 1);
  const ev = run(g, 6, 1); eq(ev.map(e => [e.id, e.on]), [["r7", day(6)]]); eq(g.rewards.unlocked.r7, day(6));
  eq(study(g, day(6)).length, 0, "second lesson same day: no re-unlock");
});
t("all four unlock at 7, 30, 60, 100 over a 100-day streak", () => {
  const g = S.newGame(); const ev = run(g, 0, 100);
  eq(ev.map(e => [e.id, e.on]), [["r7", day(6)], ["r30", day(29)], ["r60", day(59)], ["r100", day(99)]]);
  eq(S.nextReward(g, day(99)), null);
});
t("next reward: days to go + progress; counts yesterday's streak before today's lesson", () => {
  const g = S.newGame(); run(g, 0, 10); S.reconcile(g, day(10));
  const n = S.nextReward(g, day(10)); eq([n.item.id, n.current, n.toGo], ["r30", 10, 20]); eq(n.pct.toFixed(3), (10 / 30).toFixed(3));
});
t("unlocked reward stays unlocked after the streak breaks; not re-unlocked by a new 7-day streak", () => {
  const g = S.newGame(); run(g, 0, 7); g.freezes = 0;
  S.reconcile(g, day(12)); eq(S.streakInfo(g, day(12)).current, 0, "streak reset"); eq(S.rewardState(g, "r7"), "unlocked");
  eq(run(g, 12, 7).length, 0, "second 7-day run: no second unlock"); eq(g.rewards.unlocked.r7, day(6), "original date kept");
});
t("freezes count per existing rules: a frozen day bridges the streak toward 30", () => {
  const g = S.newGame(); run(g, 0, 14); eq(g.freezes, 2);
  // miss day 14 -> a freeze covers it; frozen day bridges but doesn't count, so 30 active days are needed
  const ev = run(g, 15, 16); eq(g.frozen[day(14)], true); eq(S.streakInfo(g, day(30)).current, 30);
  eq(ev.map(e => [e.id, e.on]), [["r30", day(30)]]);
});
t("claim: only when unlocked, records the date, only once; undo works", () => {
  const g = S.newGame(); eq(S.claimReward(g, "r7", day(0)), false, "locked can't be claimed"); eq(S.rewardState(g, "r7"), "locked");
  run(g, 0, 7); eq(S.claimReward(g, "r7", day(9)), true); eq(g.rewards.claimed.r7, day(9)); eq(S.rewardState(g, "r7"), "claimed");
  eq(S.claimReward(g, "r7", day(11)), false); eq(g.rewards.claimed.r7, day(9), "date not overwritten");
  S.unclaimReward(g, "r7"); eq(S.rewardState(g, "r7"), "unlocked");
});
t("edit: name/note/link/price saved; validation errors leave the item unchanged", () => {
  const g = S.newGame();
  eq(S.editReward(g, "r30", { name: "  Hoka Speedgoat 6 ", note: "size 10.5", link: "rei.com/speedgoat", price: "$155" }).ok, true);
  const r = g.rewards.items[1]; eq([r.name, r.note, r.link, r.price], ["Hoka Speedgoat 6", "size 10.5", "https://rei.com/speedgoat", 155]);
  eq(S.editReward(g, "r30", { name: "", note: "", link: "", price: "" }).error, "Name can't be empty");
  eq(S.editReward(g, "r30", { name: "X", link: "javascript:alert(1)" }).ok, false, "unsafe link rejected");
  eq(S.editReward(g, "r30", { name: "X", price: "cheap" }).error, "Price must be a number");
  eq(S.editReward(g, "r30", { name: "X", price: "-5" }).ok, false);
  eq(r.name, "Hoka Speedgoat 6", "unchanged after failed edits");
  eq(S.editReward(g, "r30", { name: "Shoes", note: "", link: "", price: "" }).ok, true); eq([r.link, r.price], ["", null], "optional fields clear");
  eq(S.editReward(g, "r100", { name: "Garmin", price: "1,299.99" }).ok, true); eq(g.rewards.items[3].price, 1299.99);
  S.resetReward(g, "r100"); eq(g.rewards.items[3].name, "GPS watch or hydration vest upgrade");
});
t("edited name doesn't change milestone or state; unlock event uses the edited name", () => {
  const g = S.newGame(); S.editReward(g, "r7", { name: "Maurten box", price: 60 });
  const ev = run(g, 0, 7); eq(ev[0].name, "Maurten box"); eq(g.rewards.items[0].days, 7);
});
t("migration: old game with no rewards gets defaults; best streak >= 7 unlocks r7 quietly", () => {
  const old = S.newGame(); run(old, 0, 8); delete old.rewards;
  const g = S.normalize(JSON.parse(JSON.stringify(old)));
  eq(g.rewards.items.length, 4); eq(g.rewards.unlocked, { r7: "earlier" }); eq(g.xp, old.xp); eq(g.active, old.active);
  const fresh = S.normalize(JSON.parse(JSON.stringify((() => { const x = S.newGame(); run(x, 0, 3); delete x.rewards; return x; })())));
  eq(fresh.rewards.unlocked, {}, "best 3: nothing unlocked");
});
t("migration from pre-streak progress replays history and unlocks historically", () => {
  const completed = {}; const lessons = [];
  for (let i = 0; i < 8; i++) { completed[`l${i}`] = day(i); lessons.push({ id: `l${i}`, kind: "lesson", exercises: [] }); }
  const g = S.migrate({ completed, ex: {} }, lessons, day(8));
  eq(g.rewards.unlocked, { r7: day(6) });
});
t("export/import round-trip keeps edits, unlock and claim dates; junk is sanitized", () => {
  const g = S.newGame(); run(g, 0, 7); S.editReward(g, "r7", { name: "Gels", link: "https://example.com", price: 42.5 }); S.claimReward(g, "r7", day(8));
  const g2 = S.normalize(JSON.parse(JSON.stringify(g)));
  eq(g2.rewards, g.rewards);
  const j = S.normalize({ rewards: { items: [{ id: "r7", name: 5, price: "x" }, { id: "bogus", name: "hack" }], unlocked: { bogus: "2026-01-01", r30: 7 }, claimed: { r60: "2026-11-01" } } });
  eq(j.rewards.items.map(r => r.id), ["r7", "r30", "r60", "r100"]); eq(j.rewards.items[0].name, "Race nutrition box (gels/chews)"); eq(j.rewards.items[0].price, null);
  eq(j.rewards.unlocked, { r60: "2026-11-01" }, "claimed implies unlocked; invalid entries dropped");
});
t("device clock moving backwards doesn't re-lock or re-unlock", () => {
  const g = S.newGame(); run(g, 0, 7); S.reconcile(g, day(3)); eq(S.rewardState(g, "r7"), "unlocked"); eq(study(g, day(3)).filter(e => e.type === "reward").length, 0);
});
console.log(`\nREWARD TESTS: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
