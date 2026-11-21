// Biblioteca mínima para gerar os .docx do pacote "artigo-revista".
// Uso: NODE_PATH=<pasta com node_modules/docx> node 01_fichamento.js
const fs = require("fs");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, AlignmentType, HeadingLevel, LevelFormat, Footer, Header,
  PageNumber, PageBreak } = D;

const AZUL = "1257A8", CINZA = "F2F4F7", AMBAR = "FFF4DB";
const FONT = "Calibri";

// **negrito** e _itálico_ inline
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const P = (t, o = {}) => new Paragraph({ children: runs(t, o.run), spacing: { after: 120, line: 276 }, alignment: o.align, indent: o.indent, keepNext: o.keepNext });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const BUL = (t, lvl = 0) => new Paragraph({ numbering: { reference: "bul", level: lvl }, children: runs(t), spacing: { after: 60, line: 264 } });
const NUM = (t, ref = "num") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 80, line: 264 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFC5CE" };
const borders = { top: border, bottom: border, left: border, right: border };
const cell = (t, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA }, borders,
  shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: String(t).split("\n").map(l => new Paragraph({ children: runs(l, { size: 19, bold: o.bold, color: o.color }), spacing: { after: 40 } })),
});
// rows: array of arrays; widths soma = 9638 (A4 com margens 2cm ~ 11906-2*1134)
function TABLE(head, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, widths[i], { fill: AZUL, bold: true, color: "FFFFFF" })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], { fill: ri % 2 ? CINZA : undefined })) })),
    ],
  });
}
// caixa de destaque (1 célula)
function BOX(title, lines, fill = AMBAR) {
  const w = 9638;
  return new Table({
    width: { size: w, type: WidthType.DXA }, columnWidths: [w],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: w, type: WidthType.DXA }, borders,
      shading: { fill, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [new Paragraph({ children: [new TextRun({ text: title, bold: true, size: 21 })], spacing: { after: 60 } }),
        ...lines.map(l => new Paragraph({ children: runs(l, { size: 20 }), spacing: { after: 60 } }))],
    })] })],
  });
}
const GAP = () => new Paragraph({ children: [], spacing: { after: 120 } });
const BREAK = () => new Paragraph({ children: [new PageBreak()] });

function build(file, title, subtitle, children) {
  const doc = new Document({
    creator: "", title,
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 44, bold: true, color: AZUL }, paragraph: { spacing: { before: 0, after: 80 } } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: AZUL }, paragraph: { spacing: { before: 320, after: 120 }, keepNext: true, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: "233B5B" }, paragraph: { spacing: { before: 240, after: 80 }, keepNext: true, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 22, bold: true, color: "233B5B" }, paragraph: { spacing: { before: 160, after: 60 }, keepNext: true, outlineLevel: 2 } },
      ],
    },
    numbering: { config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
                                   { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1000, hanging: 270 } } } }] },
      ...["num", "num2", "num3", "num4", "num5", "num6", "num7", "num8"].map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] })),
    ] },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: title + " · página ", size: 16, color: "6B7280" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "6B7280" })] })] }) },
      children: [
        new Paragraph({ style: "Title", children: [new TextRun(title)] }),
        new Paragraph({ children: [new TextRun({ text: subtitle, size: 24, color: "4B5563" })], spacing: { after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: AZUL, space: 6 } } }),
        ...children,
      ],
    }],
  });
  return Packer.toBuffer(doc).then(b => { fs.writeFileSync(file, b); console.log("ok", file); });
}
module.exports = { P, H1, H2, H3, BUL, NUM, TABLE, BOX, GAP, BREAK, build, runs };
