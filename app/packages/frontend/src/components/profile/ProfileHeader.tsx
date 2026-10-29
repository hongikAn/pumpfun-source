import { CopyAddressButton } from "./CopyAddressButton";
import { ProfileXLink } from "./ProfileXLink";
import type { LocalProfile } from "./profile-data";

function initial(name: string): string {
  return Array.from(name.trim())[0]?.toLocaleUpperCase("en-US") ?? "?";
}

/** Read-only local profile identity. Recorded external media is never requested. */
export function ProfileHeader({ profile }: { profile: LocalProfile }) {
  return (
    <header className="profile-header" data-testid="profile-header">
      <div className="profile-avatar" aria-hidden="true">
        {initial(profile.displayName)}
      </div>
      <div className="profile-identity">
        <div className="profile-title-row">
          <div>
            <p className="profile-kind">
              {profile.kind === "group"
                ? "Local group example"
                : "Local person example"}
            </p>
            <h1>{profile.displayName}</h1>
          </div>
          <span className="profile-source-chip">Synthetic identity</span>
        </div>

        <div className="profile-address-row">
          {profile.address ? (
            <>
              <code>{profile.address}</code>
              <CopyAddressButton address={profile.address} />
            </>
          ) : (
            <span>No wallet address recorded.</span>
          )}
        </div>

        {profile.bio ? (
          <p className="profile-bio">{profile.bio}</p>
        ) : (
          <p className="profile-bio profile-bio--missing">
            No local bio was recorded.
          </p>
        )}

        <ProfileXLink xUsername={profile.xUsername} />

        <dl className="profile-stats" aria-label="Local example profile counts">
          <div>
            <dt>Followers</dt>
            <dd>{profile.followers.toLocaleString("en-US")}</dd>
          </div>
          <div>
            <dt>Following</dt>
            <dd>{profile.following.toLocaleString("en-US")}</dd>
          </div>
          {profile.kind === "group" ? (
            <div>
              <dt>Members</dt>
              <dd>{profile.memberCount.toLocaleString("en-US")}</dd>
            </div>
          ) : null}
        </dl>

        {profile.hasRecordedAvatar ? (
          <p className="profile-media-note">
            A remote avatar URL exists in the seed, but offline profiles use a
            local fallback and do not request it.
          </p>
        ) : null}

        {!profile.banned ? (
          <div
            className="profile-actions"
            aria-label="Unavailable profile actions"
          >
            <button
              type="button"
              disabled
              title="Authentication and follow writes are unavailable offline"
            >
              Follow unavailable
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
