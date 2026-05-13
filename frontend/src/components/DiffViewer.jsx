export default function DiffViewer({ diff }) {
  if (!diff) return null;

  const lines = diff.split("\n");

  return (
    <div className="diff-block">
      {lines.map((line, i) => {
        let cls = "diff-line-context";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-line-add";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-line-remove";

        return (
          <span key={i} className={cls}>
            {line}
            {"\n"}
          </span>
        );
      })}
    </div>
  );
}
