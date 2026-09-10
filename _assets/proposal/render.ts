// 動画用: ロジテック物流株式会社 向けの初回商談資料を、補助線なしの SVG → HTML に描く
import fs from "node:fs";
import path from "node:path";
import { inspectRequests, pageToSvg } from "/Users/kagohashiyu-ki/work/asumo/lib/slides/inspect";
import { renderProposalDeck } from "/Users/kagohashiyu-ki/work/asumo/lib/slides/render";
import { baseCtx } from "/Users/kagohashiyu-ki/work/asumo/scripts/slides-cases";
const OUT = process.argv[2];
const ctx = baseCtx({
  companyName: "ロジテック物流株式会社",
  contactName: "高橋 誠",
  contactPosition: "採用担当",
  industry: "運輸・交通・物流・倉庫",
  useCase: "中型ドライバー",
  employeeCount: "85",
  hypotheses: [
    "求人票の給与レンジが同エリア中央値を下回っており、応募前に離脱していると推測される",
    "未経験者の定着に不安があり、研修設計まで含めた採用設計が必要と推測される",
    "採用担当が兼務で、応募者への一次連絡が翌営業日になっていると推測される",
  ],
  products: [
    {
      name: "ドライバーズワーク", pricingModel: "月額固定", unitPrice: 29800, monthsOrQty: 12,
      summary: "地域密着の配送案件に強い",
      description: "配送・運送業界に特化した求人媒体。地域ごとの求職者データベースを保有し、エリア指定での訴求が可能です。",
      strength: "地域密着,即日応募が多い,エリア指定配信",
    },
  ],
  totalUntaxed: 357600,
  ownerName: "高橋 美咲",
  ownerEmail: "misaki.takahashi@example.co.jp",
  today: "2026年09月18日",
});
const r = renderProposalDeck(ctx);
const pages = inspectRequests(r.requests, r.imageRequests, r.chartSpecs, r.decor);
pages.forEach((p, i) => {
  const svg = pageToSvg(p, { showBoxes: false });
  const f = path.join(OUT, `p${String(i + 1).padStart(2, "0")}.html`);
  fs.writeFileSync(f, `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#fff} svg{width:1440px;height:810px;display:block}</style>${svg}`, "utf8");
  console.log(`p${String(i + 1).padStart(2, "0")} ${r.sectionKeys[i] ?? ""}`);
});
console.log(`${pages.length}ページ`);
