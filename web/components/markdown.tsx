import { Fragment, type ReactNode } from 'react';

// Minimal, safe Markdown renderer for the LLM-generated prep/coach content the backend
// emits (headings, bold, bullet + numbered lists, paragraphs). React escapes all text and
// we never use dangerouslySetInnerHTML, so there is no HTML-injection surface. This keeps
// the structure the model intended (skimmable hierarchy) instead of a flat wall of text —
// without pulling in a heavy markdown dependency.

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  // Split on **bold** spans; everything else renders as plain (escaped) text.
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={`${keyPrefix}-b${i}`} className="font-semibold text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={`${keyPrefix}-t${i}`}>{part}</Fragment>;
  });
}

export function Markdown({ content, className = '' }: { content: string; className?: string }) {
  const lines = content.replace(/\r\n/g, '\n').split('\n');
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];
  let listOrdered = false;
  let key = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const items = listItems;
    const k = key++;
    if (listOrdered) {
      blocks.push(
        <ol key={`ol${k}`} className="ml-5 list-decimal space-y-1 text-slate-300">
          {items.map((it, i) => (
            <li key={i}>{renderInline(it, `ol${k}-${i}`)}</li>
          ))}
        </ol>,
      );
    } else {
      blocks.push(
        <ul key={`ul${k}`} className="ml-5 list-disc space-y-1 text-slate-300">
          {items.map((it, i) => (
            <li key={i}>{renderInline(it, `ul${k}-${i}`)}</li>
          ))}
        </ul>,
      );
    }
    listItems = [];
  };

  for (const raw of lines) {
    const trimmed = raw.trim();
    if (!trimmed) {
      flushList();
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(trimmed);
    if (heading) {
      flushList();
      const level = heading[1].length;
      const k = key++;
      // Semantic heading elements (the page already owns the single <h1>, so markdown
      // headings start at <h2>) — keeps the document outline + screen-reader nav intact.
      const inner = renderInline(heading[2], `h${k}`);
      const cls = 'mt-3 mb-1';
      if (level === 1) {
        blocks.push(
          <h2 key={`h${k}`} className={`${cls} text-lg font-bold text-slate-100`}>
            {inner}
          </h2>,
        );
      } else if (level === 2) {
        blocks.push(
          <h3 key={`h${k}`} className={`${cls} text-base font-semibold text-slate-100`}>
            {inner}
          </h3>,
        );
      } else {
        blocks.push(
          <h4 key={`h${k}`} className={`${cls} text-sm font-semibold text-slate-200`}>
            {inner}
          </h4>,
        );
      }
      continue;
    }

    const ordered = /^(\d+)[.)]\s+(.*)$/.exec(trimmed);
    if (ordered) {
      if (!listOrdered) flushList();
      listOrdered = true;
      listItems.push(ordered[2]);
      continue;
    }

    const bullet = /^[-*]\s+(.*)$/.exec(trimmed);
    if (bullet) {
      if (listOrdered) flushList();
      listOrdered = false;
      listItems.push(bullet[1]);
      continue;
    }

    flushList();
    const k = key++;
    blocks.push(
      <p key={`p${k}`} className="text-slate-300">
        {renderInline(trimmed, `p${k}`)}
      </p>,
    );
  }
  flushList();

  return <div className={`space-y-2 text-sm leading-relaxed ${className}`}>{blocks}</div>;
}
