import { StyleSheet, Text, View } from 'react-native';

import { colors, spacing } from '@/theme';

// Minimal, dependency-free Markdown renderer for the LLM-generated prep content the backend
// emits (headings, bold, bullet + numbered lists, paragraphs). Native <Text>/<View> only —
// no WebView, no html injection surface — so the model's intended structure renders as
// skimmable hierarchy instead of a flat wall of text, at parity with the web app.

function Inline({ text, style }: { text: string; style: object }) {
  // Split on **bold** spans; nested <Text> inherits the parent style and overlays bold.
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <Text style={style}>
      {parts.map((part, i) =>
        part.length > 4 && part.startsWith('**') && part.endsWith('**') ? (
          <Text key={i} style={styles.bold}>
            {part.slice(2, -2)}
          </Text>
        ) : (
          <Text key={i}>{part}</Text>
        ),
      )}
    </Text>
  );
}

type Block =
  | { kind: 'h'; level: number; text: string }
  | { kind: 'p'; text: string }
  | { kind: 'li'; ordered: boolean; index: number; text: string };

function parse(content: string): Block[] {
  const blocks: Block[] = [];
  let orderedCounter = 0;
  let inOrdered = false;

  for (const raw of content.replace(/\r\n/g, '\n').split('\n')) {
    const trimmed = raw.trim();
    if (!trimmed) {
      inOrdered = false;
      orderedCounter = 0;
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(trimmed);
    if (heading) {
      inOrdered = false;
      orderedCounter = 0;
      blocks.push({ kind: 'h', level: heading[1].length, text: heading[2] });
      continue;
    }

    const ordered = /^(\d+)[.)]\s+(.*)$/.exec(trimmed);
    if (ordered) {
      if (!inOrdered) {
        inOrdered = true;
        orderedCounter = 0;
      }
      orderedCounter += 1;
      blocks.push({ kind: 'li', ordered: true, index: orderedCounter, text: ordered[2] });
      continue;
    }

    const bullet = /^[-*]\s+(.*)$/.exec(trimmed);
    if (bullet) {
      inOrdered = false;
      orderedCounter = 0;
      blocks.push({ kind: 'li', ordered: false, index: 0, text: bullet[1] });
      continue;
    }

    inOrdered = false;
    orderedCounter = 0;
    blocks.push({ kind: 'p', text: trimmed });
  }
  return blocks;
}

export function Markdown({ content }: { content: string }) {
  const blocks = parse(content);
  return (
    <View style={styles.root}>
      {blocks.map((b, i) => {
        if (b.kind === 'h') {
          const style =
            b.level === 1 ? styles.h1 : b.level === 2 ? styles.h2 : styles.h3;
          return <Inline key={i} text={b.text} style={style} />;
        }
        if (b.kind === 'li') {
          return (
            <View key={i} style={styles.liRow}>
              <Text style={styles.liMarker}>{b.ordered ? `${b.index}.` : '•'}</Text>
              <Inline text={b.text} style={styles.liText} />
            </View>
          );
        }
        return <Inline key={i} text={b.text} style={styles.p} />;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { gap: spacing.sm },
  bold: { fontWeight: '700', color: colors.text },
  h1: { color: colors.text, fontSize: 18, fontWeight: '800', marginTop: spacing.sm },
  h2: { color: colors.text, fontSize: 16, fontWeight: '700', marginTop: spacing.sm },
  h3: { color: colors.text, fontSize: 14, fontWeight: '700', marginTop: spacing.xs },
  p: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },
  liRow: { flexDirection: 'row', gap: spacing.sm, paddingRight: spacing.sm },
  liMarker: { color: colors.primary, fontSize: 14, lineHeight: 21, minWidth: 18 },
  liText: { color: colors.textMuted, fontSize: 14, lineHeight: 21, flex: 1 },
});
