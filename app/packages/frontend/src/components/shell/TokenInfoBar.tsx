'use client';

import { useRef, useState, type KeyboardEvent } from 'react';
import {
  InfoBarFollowingIcon,
  InfoBarPositionsIcon,
  InfoBarRecentIcon,
  InfoBarSettingsIcon,
  InfoBarWatchlistIcon,
} from './captured-icons';

const VIEWS = [
  { label: 'Watchlist', icon: InfoBarWatchlistIcon },
  { label: 'Positions', icon: InfoBarPositionsIcon },
  { label: 'Following', icon: InfoBarFollowingIcon },
  { label: 'Recently viewed', icon: InfoBarRecentIcon },
] as const;

/** Placeholder count in the captured pre-hydration ticker. */
const SKELETON_ITEMS = 14;

const RADIO_BASE =
  'flex size-6 shrink-0 items-center justify-center rounded-sm transition-colors hover:bg-bg-tertiary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent';
const RADIO_CHECKED = `${RADIO_BASE} bg-bg-tertiary text-text-primary`;
const RADIO_UNCHECKED =
  'flex size-6 shrink-0 items-center justify-center rounded-sm text-text-quaternary transition-colors hover:bg-bg-tertiary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent';

const NEXT_KEYS = new Set(['ArrowRight', 'ArrowDown']);
const PREVIOUS_KEYS = new Set(['ArrowLeft', 'ArrowUp']);

/**
 * The token info bar under the top bar. Its view switch works locally; the ticker
 * keeps the captured loading state because coin data needs the market-discovery
 * API, which is not implemented. Settings open a dialog upstream and are disabled.
 */
export function TokenInfoBar() {
  const [selected, setSelected] = useState(0);
  const radios = useRef<Array<HTMLButtonElement | null>>([]);

  function select(index: number) {
    const next = (index + VIEWS.length) % VIEWS.length;
    setSelected(next);
    radios.current[next]?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (NEXT_KEYS.has(event.key)) select(index + 1);
    else if (PREVIOUS_KEYS.has(event.key)) select(index - 1);
    else if (event.key === 'Home') select(0);
    else if (event.key === 'End') select(VIEWS.length - 1);
    else return;
    event.preventDefault();
  }

  return (
    <div
      data-testid="token-info-bar"
      className="flex h-7 items-center gap-3 border-t border-border-secondary bg-bg-primary px-[var(--padding-x-main)] max-lg:px-4 max-md:hidden"
    >
      <div className="flex shrink-0 items-center gap-0.5">
        <button
          type="button"
          aria-label="Info bar settings"
          aria-haspopup="dialog"
          disabled
          title="Info bar settings are not implemented in this reconstruction"
          data-state="closed"
          className="flex size-6 shrink-0 items-center justify-center rounded-sm text-text-quaternary transition-colors hover:bg-bg-tertiary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent data-[state=open]:bg-bg-tertiary data-[state=open]:text-text-primary"
        >
          <InfoBarSettingsIcon />
        </button>
        <div role="radiogroup" aria-label="Info bar content" className="flex shrink-0 items-center gap-0.5">
          {VIEWS.map((view, index) => {
            const checked = index === selected;
            const ViewIcon = view.icon;
            return (
              <button
                key={view.label}
                ref={(element) => {
                  radios.current[index] = element;
                }}
                type="button"
                role="radio"
                aria-checked={checked}
                aria-label={view.label}
                tabIndex={checked ? 0 : -1}
                onClick={() => setSelected(index)}
                onKeyDown={(event) => onKeyDown(event, index)}
                className={checked ? RADIO_CHECKED : RADIO_UNCHECKED}
              >
                <ViewIcon />
              </button>
            );
          })}
        </div>
      </div>
      <span aria-hidden="true" className="h-3.5 w-px shrink-0 bg-border-secondary" />
      <div className="scrollbar-hide flex h-full min-w-0 flex-1 items-center gap-3 overflow-x-auto">
        <div aria-hidden="true" className="flex h-full w-full items-center gap-3 overflow-hidden">
          {Array.from({ length: SKELETON_ITEMS }, (_, index) => (
            <span key={index} className="flex shrink-0 items-center gap-1.5 px-1.5">
              <span className="size-4 animate-pulse rounded-sm bg-bg-quaternary" />
              <span className="h-3 w-12 animate-pulse rounded bg-bg-quaternary" />
              <span className="h-3 w-10 animate-pulse rounded bg-bg-tertiary" />
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
