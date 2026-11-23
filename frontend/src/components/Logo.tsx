export default function Logo({
  size = 36,
  showText = true,
}: {
  size?: number;
  showText?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        aria-hidden="true"
        focusable="false"
      >
        <rect width="48" height="48" rx="12" fill="#2D6A4F" />
        <polyline
          points="10,34 18,24 26,28 38,14"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <polyline
          points="31,14 37,14 37,20"
          fill="none"
          stroke="#168AAD"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {showText && (
        <span className="font-sora font-semibold text-lg text-ink">DueSense AI</span>
      )}
    </div>
  );
}
