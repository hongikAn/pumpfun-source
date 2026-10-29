"use client";

/** Captured 875737 username branch; placement in the local profile is authored. */
export function ProfileXLink({ xUsername }: { xUsername: string | null }) {
  const username = (xUsername?.trim() || "").replace(/^@/, "");
  if (!username) return null;

  const label = `@${username} on X`;
  return (
    <a
      href={`https://x.com/${encodeURIComponent(username)}`}
      target="_blank"
      rel="noreferrer"
      aria-label={label}
      data-testid="user-x-badge"
      className="inline-flex max-w-full break-all text-sm text-text-tertiary hover:text-text-primary hover:underline"
      onClick={(event) => event.stopPropagation()}
    >
      {label}
    </a>
  );
}
