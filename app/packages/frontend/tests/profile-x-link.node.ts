import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ProfileXLink } from "../src/components/profile/ProfileXLink";

const render = (xUsername: string | null) =>
  renderToStaticMarkup(createElement(ProfileXLink, { xUsername }));

test("omits missing, blank and a lone @ identity", () => {
  for (const value of [null, "", "   ", " @ "]) assert.equal(render(value), "");
});

test("trims and removes exactly one leading @ as the captured badge does", () => {
  const html = render("  @alice_on_x  ");
  assert.match(html, /href="https:\/\/x.com\/alice_on_x"/);
  assert.match(html, /aria-label="@alice_on_x on X"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noreferrer"/);
  assert.match(render("@@alice"), /href="https:\/\/x.com\/%40alice"/);
});

test("encodes the complete username as one path segment without guessing validation", () => {
  const html = render("a/b?c#d&é");
  assert.match(html, /href="https:\/\/x.com\/a%2Fb%3Fc%23d%26%C3%A9"/);
  assert.match(html, /@a\/b\?c#d&amp;é on X/);
  assert.match(
    render("x.com/example"),
    /href="https:\/\/x.com\/x.com%2Fexample"/,
  );
});
