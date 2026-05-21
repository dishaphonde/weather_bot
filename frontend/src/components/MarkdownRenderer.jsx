import React from 'react';

export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  // Simple token parser that safely translates markdown-like syntax to React elements.
  // This is highly robust and performs perfectly with streaming (partial tokens).
  const parseMarkdown = (text) => {
    // Normalize newlines
    const lines = text.replace(/\r\n/g, '\n').split('\n');
    const elements = [];
    let inList = false;
    let listItems = [];
    let isCodeBlock = false;
    let codeContent = [];
    let inTable = false;
    let tableRows = [];

    const flushList = (key) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${key}`} className="list-disc pl-6 mb-4 space-y-1 text-slate-300">
            {listItems.map((item, idx) => (
              <li key={idx}>{parseInline(item)}</li>
            ))}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    const flushCodeBlock = (key) => {
      if (codeContent.length > 0) {
        elements.push(
          <pre key={`code-${key}`} className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl text-xs font-mono text-indigo-300 overflow-x-auto my-3 scrollbar-thin">
            <code>{codeContent.join('\n')}</code>
          </pre>
        );
        codeContent = [];
        isCodeBlock = false;
      }
    };

    const flushTable = (key) => {
      if (tableRows.length > 0) {
        // Simple table parser
        const headers = tableRows[0];
        const rows = tableRows.slice(2); // Skip separator row (idx 1)
        
        elements.push(
          <div key={`table-${key}`} className="overflow-x-auto my-4 rounded-xl border border-slate-800 bg-slate-900/40 glow-indigo">
            <table className="min-w-full divide-y divide-slate-800">
              <thead className="bg-slate-900/80">
                <tr>
                  {headers.map((h, idx) => (
                    <th key={idx} className="px-4 py-2 text-left text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                      {parseInline(h.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-800/30 transition-colors duration-150">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-4 py-2 text-sm whitespace-nowrap">
                        {parseInline(cell.trim())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
        inTable = false;
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code Block Trigger
      if (line.startsWith('```')) {
        if (isCodeBlock) {
          flushCodeBlock(i);
        } else {
          // If we had lists or tables, flush them first
          flushList(i);
          flushTable(i);
          isCodeBlock = true;
        }
        continue;
      }

      if (isCodeBlock) {
        codeContent.push(line);
        continue;
      }

      // Markdown Table Trigger (starts and ends/contains pipe characters)
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        flushList(i);
        inTable = true;
        // Parse cells split by '|'
        const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        tableRows.push(cells);
        continue;
      } else if (inTable) {
        flushTable(i);
      }

      // Headers
      if (line.startsWith('# ')) {
        flushList(i);
        elements.push(<h1 key={i} className="text-2xl font-bold text-indigo-400 mt-4 mb-2">{parseInline(line.substring(2))}</h1>);
      } else if (line.startsWith('## ')) {
        flushList(i);
        elements.push(<h2 key={i} className="text-xl font-bold text-slate-100 mt-4 mb-2 border-b border-slate-800 pb-1">{parseInline(line.substring(3))}</h2>);
      } else if (line.startsWith('### ')) {
        flushList(i);
        elements.push(<h3 key={i} className="text-lg font-bold text-indigo-400 mt-3 mb-1.5">{parseInline(line.substring(4))}</h3>);
      } 
      // Bullet list items
      else if (line.startsWith('- ') || line.startsWith('* ')) {
        inList = true;
        listItems.push(line.substring(2));
      } 
      // Empty lines
      else if (line.trim() === '') {
        flushList(i);
        // Add spacing instead of empty p tags
      } 
      // Normal paragraph text
      else {
        flushList(i);
        elements.push(
          <p key={i} className="text-sm md:text-base text-slate-300 leading-relaxed mb-3">
            {parseInline(line)}
          </p>
        );
      }
    }

    // Flush any remaining active structures
    flushList(lines.length);
    flushCodeBlock(lines.length);
    flushTable(lines.length);

    return elements;
  };

  // Helper to parse inline tokens like bold (**), italic (*), and inline code (`)
  const parseInline = (text) => {
    if (!text) return '';
    
    // Simple inline parser
    const tokens = [];
    let currentIdx = 0;
    
    // Pattern to search for bold (**), inline code (`), and bold alternative (__)
    const regex = /(\*\*|`|__)(.*?)\1/g;
    let match;
    
    while ((match = regex.exec(text)) !== null) {
      const matchIdx = match.index;
      const type = match[1];
      const content = match[2];
      
      // Push preceding plain text
      if (matchIdx > currentIdx) {
        tokens.push(text.substring(currentIdx, matchIdx));
      }
      
      // Push formatted text
      if (type === '**' || type === '__') {
        tokens.push(<strong key={matchIdx} className="font-bold text-indigo-300">{content}</strong>);
      } else if (type === '`') {
        tokens.push(<code key={matchIdx} className="px-1.5 py-0.5 bg-slate-950/80 rounded border border-slate-800 text-indigo-400 font-mono text-xs">{content}</code>);
      }
      
      currentIdx = regex.lastIndex;
    }
    
    // Push remaining text
    if (currentIdx < text.length) {
      tokens.push(text.substring(currentIdx));
    }
    
    return tokens.length > 0 ? tokens : text;
  };

  return <div className="prose-custom w-full max-w-none text-slate-300">{parseMarkdown(content)}</div>;
}
