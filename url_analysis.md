# Analysis of PR #87: Fragment-Based MSF URL Structure

## Overview

**PR:** [#87 - Document fragment-based MSF URL structure](https://github.com/moq-wg/msf/pull/87)
**Author:** Will Law (@wilaw)
**Status:** Open
**Related Issues:** #60 (primary), #72 (prior approach)
**Related Cross-Repo Work:** moq-wg/moq-transport#1355 (name formatting)

---

## Problem Statement

The core problem (documented in Issue #60) is the need for a unified URL format that allows Content Management Systems and applications to communicate:

1. **Connection endpoint**: A WebTransport/QUIC connection to a MOQT distribution network (MDN)
2. **Track identifier**: A WARP/MSF catalog track for subscription

Currently, there is no standardized way to represent both pieces of information in a single URL. This creates interoperability challenges for:
- CMS systems generating playback URLs
- Player applications parsing and connecting to streams
- Deep-linking to specific content within a broadcast

---

## Proposed Design (PR #87)

PR #87 proposes a **fragment-based URL structure** where:

### URL Components

```
[scheme]://[authority]/[path]?[query]#[namespace-tuple]--[track-name]
```

- **Scheme**: `moqt://` for native MOQT, or `https://` for WebTransport
- **Authority**: Host and optional port (default 443)
- **Path**: Server configuration/relay identifier
- **Query**: Reserved parameters (`location-range`, `c4m` for auth tokens)
- **Fragment**: Namespace tuple + track name, separated by `--`

### Namespace/Track Encoding (from moq-transport#1355)

- Namespace tuple components separated by single hyphen (`-`)
- Namespace and track name separated by double hyphen (`--`)
- Non-alphanumeric characters percent-encoded (`%xx`)

### Example URLs

```
# WebTransport with catalog
https://example.com/server/config?a=1&b=2#customer-livestream-123--catalog

# Raw QUIC connection
moqt://example.com/relay-app/relayID#customerID-broadcastID--catalog

# Non-catalog track reference
https://example.com/relay-app/relayID#customerID-broadcastID--video

# With location range
https://example.com/relay-app/relayID?location-range=34-0-64-16#...
```

### Reserved Query Parameters

| Parameter | Purpose |
|-----------|---------|
| `location-range` | MOQT Location tuples (Group ID-Object ID pairs) |
| `c4m` | Authentication tokens |

---

## Pros

### 1. Clean Separation of Concerns
The fragment portion is stripped before the WebTransport CONNECT request, allowing the URL to serve dual purposes: connection establishment and content identification.

### 2. Standards Compliance
- Fragments are explicitly excluded from HTTP requests per RFC 3986
- WebTransport specs forbid fragments in connection requests, making this a natural fit
- The approach respects existing web architecture semantics

### 3. Prevents Accidental HTTP Requests
Using `moqt://` scheme (or fragments that are stripped) prevents issues like:
- Slack/Discord link previews triggering HTTP requests
- Browsers attempting standard HTTP fetches
- Middleware/proxies misinterpreting the URLs

### 4. Alignment with Transport Layer Work
The encoding scheme (`-` for namespace tuples, `--` for track separator) aligns with moq-transport#1355, ensuring consistency across specs for logging, file naming, and URL construction.

### 5. Backward Compatibility
- The `moqt://` to `https://` conversion is straightforward
- Existing URL parsing libraries can handle the structure
- Fragment-based approach doesn't interfere with query parameters for other purposes

---

## Cons

### 1. Separator Ambiguity (Major Concern)
**Raised by @michalhosna**: Using identical separators (`-`) with optional values creates parsing ambiguity.

Example problem:
```
#a-b-c--track
```
Is this `namespace=[a,b,c]` or `namespace=[a-b,c]` or something else?

**Proposed mitigation**: Use different separators for MOQT locations (e.g., periods: `34.0-64.16`)

### 2. Escaping Complexity
- Namespace values containing hyphens require percent-encoding
- Real-world namespaces often use hyphens (e.g., `customer-123`, `live-stream-id`)
- This leads to URLs like: `#customer%2D123-broadcast%2D456--catalog`

### 3. Fragment Limitations
- Only one fragment allowed per URL (RFC 3986)
- Cannot easily represent multiple tracks in a single URL
- Limited expressiveness compared to query parameters

### 4. Query vs Fragment Debate Unresolved
PR #72 (the prior approach) used query parameters (`ns=`, `t=`), which:
- Offer better extensibility
- Allow multiple distinct parameters
- Have clearer parsing semantics

The switch to fragments in PR #87 isn't fully justified against these benefits.

### 5. Protocol Discovery Ambiguity
**Raised by @vasilvv**: The URL intentionally omits explicit protocol specification (WebTransport vs. raw QUIC), which contradicts RFC 3986 principles that URLs should identify the mechanism to locate resources.

### 6. Object ID Handling Unclear
The `location-range` format (`34-0-64-16`) is ambiguous:
- Is Object ID always required?
- How are open ranges represented?
- Should Object ID default to 0 if omitted?

---

## Alternative Approaches Considered

### Option A: Query Parameter Approach (PR #72)

```
moqt://example.com/relay-app/relayID?ns=customerID/broadcastID&t=video
```

**Pros:**
- Clear parameter semantics
- Better extensibility
- Multiple parameters without ambiguity

**Cons:**
- Query strings have MIME-type associations
- Less clean separation between connection and content

### Option B: Reserved Path Separator (Issue #60 Option 3)

```
https://mdn.com/customerID/appID/!/example.com/live/broadcastID/catalog
```

**Pros:**
- All information in path
- No fragment/query complexity

**Cons:**
- Non-standard path semantics
- Harder to parse
- Could conflict with actual path components

### Option C: Base64-Encoded Fragment

```
https://example.com/path#<base64-encoded-track-info>
```

**Pros:**
- Avoids escaping issues
- Any characters allowed in encoded payload

**Cons:**
- Not human-readable
- Debugging difficulty
- Larger URLs

---

## Comprehensive Discussion Summary

This section summarizes key discussions from Issue #60 (31 comments), PR #72, PR #87, and related Issue #65.

### The Evolution of the URL Design (Issue #60)

**Phase 1: Initial Proposals**
Will Law (@wilaw) originally proposed three approaches:
1. Out-of-band information (rejected as fragile for interoperability)
2. Reserved first path segment for connection data
3. Reserved path separator (`!`) as divider

**Phase 2: Fragment-Based Emergence**
Victor Vasiliev (@vasilvv) suggested fragments with base64 encoding. Will Law countered with human-readable fragments, proposing to constrain WARP track names to exclude `#`, `?`, `&`:
```
https://mdn.com/customerID/appID?warptoken=12345#example.com/live/broadcastID/catalog
```

**Phase 3: WebTransport Mechanics Clarification**
Afrind questioned how fragments behave in WebTransport CONNECT requests. Will clarified that:
- Fragments are stripped before connection establishment
- Players issue separate SUBSCRIBE commands post-connection
- This creates clean separation between "where to connect" and "what to subscribe to"

**Phase 4: Scheme Debate**
Michal Hošna challenged using HTTPS scheme:
- **Concern**: HTTPS endpoints receive unwanted GET/HEAD requests (link previews, crawlers)
- **Will's response**: Browsers require HTTPS for WebTransport, but custom schemes work for non-browser clients
- **Resolution**: The `moqt://` scheme emerged as the compromise - convertible to HTTPS for browsers, but distinct enough to prevent accidental HTTP requests

**Phase 5: Final Consensus (October 1 hallway discussions)**
The group converged on:
```
moqt://authority/path?query#namespace/track
```
With explicit conversion rules for WebTransport clients.

### The Query vs Fragment Debate (PR #72 → PR #87)

PR #72 used query parameters (`?ns=...&t=...`), but faced these challenges:

**Query Stripping Conflict (@michalhosna)**
- MOQT spec transmits query portions in SETUP parameters
- PR #72 stripped queries before server transmission
- This deviated from existing specifications
- A custom scheme would sidestep this incompatibility

**Extensibility Arguments**
Will Law argued for queries:
- Better extensibility for future parameters
- Multiple distinct parameters require clear parsing rules
- Fragments can only appear once per URL
- Fragments have MIME-type associations inappropriate for metadata

**Fragment Arguments (@vasilvv, @michalhosna)**
- Fragments provide cleaner semantics for resource subsetting
- RFC 3986 defines fragments as "secondary resource identification"
- moq-transport#1355 established fragment-compatible encoding

**The Switch to Fragments (PR #87)**
PR #87 moved namespace+track to fragments, keeping query for modifiers like `location-range` and `c4m`. This hybrid approach attempts to satisfy both camps.

### Technical Edge Cases (Raised in PR #72, still open)

**Escaping Ambiguities (@michalhosna)**
- How are forward slashes escaped within namespace tuple values?
- Are zero-length tuple components permitted? (e.g., `//a//`)
- Can `/` be encoded as `%2F`? How does this interact with tuple parsing?
- What about namespace values containing hyphens?

**Range Semantics**
- Open-ended range support needed (`34-` for "from group 34 onwards")
- Timescale consistency with catalog definitions
- How do ranges apply to non-catalog tracks?

**Protocol Discovery**
RFC 3986: "A URL provides means of locating resources by describing access mechanisms."
The current design intentionally omits protocol (WebTransport vs QUIC), relying on:
- Client capability detection
- ALPN negotiation
This contradicts strict RFC interpretation but enables practical flexibility.

### Authentication Token Handling (Issue #65)

**Problem**: CAT-4-MOQT#21 removed token URL guidance, leaving a gap.

**Proposed Solution**: Reserved `c4m` query parameter with base64-encoded tokens.

**Open Question** (@gwendalsimon): What about multiple tokens (auth, ad, watermark)?
- Suggestion: Repeat `c4m` parameter multiple times
- No formal resolution yet

### Cross-Specification Alignment

**moq-transport#1355** established encoding rules that PR #87 adopts:
- Alphanumerics, hyphens, underscores unescaped
- Single hyphen (`-`) separates namespace tuple components
- Double hyphen (`--`) separates namespace from track name
- Non-alphanumeric bytes percent-encoded (`%xx`)

This ensures consistency between:
- URL fragments
- Log file formatting
- File naming conventions

### Key Participants and Their Positions

| Participant | Role | Key Position |
|-------------|------|--------------|
| @wilaw | Author | Human-readable URLs, practical interoperability |
| @vasilvv | CONTRIBUTOR | Fragment-based, standards alignment |
| @michalhosna | Reviewer | Technical rigor, edge case coverage |
| @gwendalsimon | Reviewer | Documentation consistency, multi-token support |
| @afrind | Contributor | WebTransport mechanics clarification |

### Unresolved Issues Across All Discussions

1. **Separator syntax**: Same `-` character used for multiple purposes
2. **Escaping rules**: Incomplete specification for special characters
3. **Zero-length components**: Undefined behavior for `//a//`
4. **Open ranges**: No syntax for unbounded ranges
5. **Protocol hints**: No standard way to require specific transport
6. **Multi-token auth**: No formal specification for multiple `c4m` values
7. **Non-catalog tracks**: How do time ranges apply without catalog context?

---

## Reviewer Concerns Summary

| Reviewer | Concern | Source | Status |
|----------|---------|--------|--------|
| @michalhosna | Separator ambiguity with `-` | PR #87 | Open |
| @michalhosna | Forward slash escaping in tuples | PR #72 | Open |
| @michalhosna | Zero-length component handling | PR #72 | Open |
| @michalhosna | Object ID default value | PR #87 | Open |
| @michalhosna | Query stripping vs MOQT spec | PR #72 | Moved to fragments |
| @vasilvv | Protocol specification omission | PR #72 | Open |
| @vasilvv | URL scope (MSF vs MOQT spec) | PR #72 | Open |
| @gwendalsimon | Documentation inconsistencies | PR #72, #87 | Partially addressed |
| @gwendalsimon | Multiple token handling | Issue #65 | Open |

---

## Recommendations

### 1. Adopt Different Separators for Location Components

Use periods (`.`) for Group/Object ID separation within location-range:
```
?location-range=34.0-64.16
```
This clearly distinguishes:
- `-` for namespace tuple boundaries
- `--` for namespace/track separation
- `.` for Group.Object within locations

### 2. Specify Object ID Default Behavior

Explicitly state that Object ID defaults to `0` when omitted:
```
?location-range=34-64  // Equivalent to 34.0-64.0
```

### 3. Consider Hybrid Approach

Keep fragment for namespace+track (which are "resource identifiers" per URI semantics) but move `location-range` and `c4m` to query parameters (which are "modifiers" per URI semantics):

```
moqt://example.com/relay#customerID-broadcastID--video?location-range=34.0-64.16&c4m=token
```

This aligns better with RFC 3986 semantics:
- Fragment = resource identification (what content)
- Query = resource modification (what part, how to access)

### 4. Document Escaping Rules Explicitly

Provide clear examples of:
- Namespace values with hyphens: `my%2Dapp-namespace--track`
- Track names with special characters
- Unicode handling

### 5. Add Protocol Discovery Mechanism

Consider adding an optional query parameter for protocol hints:
```
?proto=wt  // WebTransport
?proto=quic  // Raw QUIC
```

Or rely on scheme:
- `moqt://` = implementation chooses
- `moqt+wt://` = WebTransport required
- `moqt+quic://` = Raw QUIC required

---

## Conclusion

PR #87 represents a reasonable evolution from PR #72, moving from query-based to fragment-based track identification. The fragment approach has merit for its clean separation between connection establishment and content identification.

However, the current proposal has significant parsing ambiguity issues that should be resolved before merging:

1. **Critical**: Separator ambiguity needs resolution (different separators for different purposes)
2. **Important**: Object ID default behavior needs specification
3. **Recommended**: Escaping rules need explicit documentation with examples

The hybrid approach (fragment for namespace+track, query for modifiers) may offer the best of both worlds while aligning with URI semantics standards.

---

## A Better Approach: Synthesis

Based on all the discussions, here is a synthesized proposal that addresses the major concerns:

### Proposed URL Structure

```
moqt://authority/path?[query]#namespace--track
```

Where:
- **Scheme**: `moqt://` (converts to `https://` for WebTransport)
- **Fragment**: Contains namespace tuple and track name only
- **Query**: Contains all modifiers (ranges, tokens)

### Key Design Decisions

**1. Use Distinct Separators Throughout**

| Purpose | Separator | Example |
|---------|-----------|---------|
| Namespace tuple fields | `/` | `example.com/live/broadcast` |
| Namespace-track boundary | `--` | `example.com/live/broadcast--video` |
| Location Group.Object | `.` | `34.0` |
| Location range | `-` | `34.0-64.16` |

This eliminates the ambiguity of using `-` for multiple purposes.

**2. Fragment Contains Only Resource Identification**

```
#example.com/live/broadcast--catalog
```

- Uses `/` as tuple separator (natural for hierarchical names)
- `--` clearly marks the boundary to track name
- Aligns with URI semantics (fragment = resource identification)

**3. Query Contains Only Modifiers**

```
?start=34.0&end=64.16&c4m=token1&c4m=token2
```

- Explicit parameter names (`start`, `end`) instead of packed `location-range`
- Multiple `c4m` values allowed for multiple tokens
- Query is transmitted to server per MOQT spec (no stripping conflict)

**4. Explicit Escaping Rules**

| Character | Escape | Example |
|-----------|--------|---------|
| `/` in value | `%2F` | `my%2Fpath` for literal "my/path" |
| `-` in value | `%2D` | `customer%2D123` for "customer-123" |
| `--` in value | `%2D%2D` | Always escaped to prevent false boundaries |

**5. Optional Protocol Hints**

For cases where specific transport is required:
```
moqt://example.com/path?proto=wt#ns--track    // Require WebTransport
moqt://example.com/path?proto=quic#ns--track  // Require raw QUIC
```

### Complete Example

```
moqt://relay.example.com:4433/customer-app?start=1000.0&end=2000.15&c4m=eyJhbGciOiJIUzI1NiJ9#example.com/live/sports%2Fgame123--video
```

Breakdown:
- Connect to: `relay.example.com:4433/customer-app`
- Subscribe to namespace: `["example.com", "live", "sports/game123"]` (note escaped `/`)
- Track name: `video`
- Location range: Group 1000 Object 0 to Group 2000 Object 15
- Auth token: `eyJhbGciOiJIUzI1NiJ9`

### Why This is Better

1. **No Separator Ambiguity**: Each separator has exactly one purpose
2. **Standards Aligned**: Fragment for identification, query for modification
3. **MOQT Compatible**: Query parameters transmitted as-is
4. **Human Readable**: Clear structure, natural hierarchy
5. **Extensible**: New query parameters can be added without fragment changes
6. **Multi-Token Support**: Multiple `c4m` parameters allowed
7. **Clear Escaping**: Simple rules with no edge case ambiguity

### Migration Path from PR #87

| PR #87 Syntax | Proposed Syntax |
|---------------|-----------------|
| `#customerID-broadcastID--catalog` | `#customerID/broadcastID--catalog` |
| `?location-range=34-0-64-16` | `?start=34.0&end=64.16` |
| `?c4m=token` | `?c4m=token` (unchanged) |

The main change is replacing `-` with `/` for namespace tuples in fragments, which:
- Matches natural path-like semantics
- Avoids conflicts with hyphenated names
- Aligns better with how namespaces are typically structured

---

## Conclusion

PR #87 represents significant progress in standardizing MSF URLs, but several technical issues remain unresolved. The fragment-based approach is sound, but the separator scheme creates parsing ambiguity.

**Recommendation**: Before merging PR #87:
1. Resolve the separator ambiguity (adopt `/` for namespace tuples)
2. Specify explicit escaping rules with examples
3. Define Object ID default behavior
4. Consider explicit parameter names for location ranges
5. Address the multi-token authentication use case

The working group should consider whether a cleaner redesign (as proposed above) is worth the additional iteration versus iterating on PR #87's current structure.

---

## Additional Proposal A: Single `moq://` Scheme with Standards Analysis

This proposal advocates for a unified `moq://` scheme (without the 't') that simplifies the URL structure while maintaining full compliance with URI standards.

### Proposed URL Structure

```
moq://authority[:port]/path#namespace/track[?query]
```

**Key difference**: A single `moq://` scheme that encompasses all MOQT transport mechanisms, with protocol negotiation handled at the connection layer rather than the URL layer.

### How This Aligns with URL Specification Standards

#### RFC 3986 Compliance Analysis

**1. Scheme Component (Section 3.1)**

RFC 3986 states: *"Scheme names consist of a sequence of characters beginning with a letter and followed by any combination of letters, digits, plus (+), period (.), or hyphen (-)."*

- `moq` is valid: starts with letter, uses only lowercase letters
- Shorter than `moqt`, reducing URL length
- Follows the convention of common schemes (`http`, `ftp`, `ssh`)

**2. Hierarchical vs Opaque URIs (Section 3)**

The `moq://` scheme uses hierarchical structure with authority:
```
moq://[userinfo@]host[:port]/path
```

This aligns with RFC 3986's hierarchical URI model where:
- Authority identifies the server endpoint
- Path identifies relay/application configuration
- Fragment identifies the content resource

**3. Fragment Semantics (Section 3.5)**

RFC 3986: *"The fragment identifier component...is not part of a scheme's absolute URI; rather it is indirect identification of a secondary resource by reference to a primary resource."*

Using fragments for namespace/track is semantically correct:
- Primary resource = MOQT connection endpoint
- Secondary resource = specific track within that connection

#### IANA URI Scheme Registration

For `moq://` to become official, IANA registration would require:

| Field | Value |
|-------|-------|
| Scheme name | moq |
| Status | Provisional → Permanent |
| Applications/protocols | Media over QUIC Transport |
| Contact | IETF MOQ Working Group |
| Change controller | IESG |
| References | draft-ietf-moq-transport, draft-ietf-moq-msf |

**Registration Category**: The scheme would be "Permanent" given IETF backing.

### Protocol Negotiation Model

Instead of encoding transport in the URL, `moq://` uses connection-time negotiation:

```
┌─────────────────────────────────────────────────────────────┐
│ Client parses: moq://relay.example.com/app#ns/broadcast--v  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: DNS Resolution                                      │
│   - Check for HTTPS RR (indicates HTTP/3 support)           │
│   - Check for SVCB records with alpn hints                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Connection Attempt (based on client capability)     │
│                                                             │
│   Browser Client:                                           │
│     → Convert to https://relay.example.com/app              │
│     → Initiate WebTransport over HTTP/3                     │
│                                                             │
│   Native Client:                                            │
│     → Attempt raw QUIC with ALPN "moq-00"                   │
│     → Fallback to WebTransport if needed                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: MOQT SETUP exchange (same regardless of transport)  │
└─────────────────────────────────────────────────────────────┘
```

### Differences from Current `moqt://` Approach

| Aspect | Current (`moqt://`) | Proposed (`moq://`) |
|--------|---------------------|---------------------|
| Scheme length | 4 chars | 3 chars |
| Transport encoding | Implicit/ambiguous | Explicitly out-of-band |
| Browser handling | Requires conversion to `https://` | Same conversion rule |
| Scheme registration | Not yet registered | Would require registration |
| Extensibility | Protocol embedded in scheme | Protocol in negotiation |

### How `moq://` Changes URL Specification Interpretation

**1. Scheme-to-Protocol Mapping**

Traditional interpretation: One scheme = one protocol
- `http://` → HTTP/1.1 or HTTP/2
- `https://` → HTTP/1.1 or HTTP/2 over TLS

New interpretation with `moq://`: One scheme = one application protocol, multiple transports
- `moq://` → MOQT over WebTransport OR MOQT over raw QUIC

This follows the precedent set by `https://` supporting HTTP/2 and HTTP/3 under the same scheme.

**2. Default Port Assignment**

RFC 3986 requires schemes to specify default ports. Proposal:

```
moq://example.com/path     → port 443 (same as HTTPS/WebTransport)
moq://example.com:4433/path → explicit port
```

Using port 443 as default:
- Maximizes firewall traversal
- Aligns with WebTransport expectations
- May conflict with existing HTTPS services (requires careful deployment)

Alternative: Register a dedicated port (e.g., 4433) for raw QUIC MOQT.

**3. Security Considerations**

RFC 7595 (URI Scheme Guidelines) requires security analysis:

- **Confidentiality**: Underlying QUIC provides TLS 1.3 encryption
- **Integrity**: QUIC's authenticated encryption protects data
- **Authentication**: Delegated to `c4m` tokens and server certificates
- **Phishing risk**: Custom scheme reduces accidental HTTP requests

### Confirmation of Standards Compliance

| Standard | Requirement | `moq://` Compliance |
|----------|-------------|---------------------|
| RFC 3986 | Valid scheme syntax | ✅ Lowercase letters only |
| RFC 3986 | Hierarchical URI structure | ✅ authority/path/fragment |
| RFC 3986 | Fragment semantics | ✅ Secondary resource ID |
| RFC 7595 | Registration template | ✅ Can be completed |
| RFC 7595 | Security considerations | ✅ TLS 1.3 via QUIC |
| RFC 7595 | Interoperability | ⚠️ Requires client coordination |

### Complete Example with `moq://`

```
moq://relay.cdn.example:443/customer-app?c4m=eyJhbGciOiJFUzI1NiJ9#acme.com/live/sports--catalog
```

Parsing:
- **Scheme**: `moq` (MOQT protocol family)
- **Authority**: `relay.cdn.example:443`
- **Path**: `/customer-app` (relay configuration)
- **Query**: `c4m=eyJhbGciOiJFUzI1NiJ9` (auth token)
- **Fragment**: `acme.com/live/sports--catalog` (namespace + track)

Client behavior:
1. Browser → converts to `https://relay.cdn.example:443/customer-app`, initiates WebTransport
2. Native app → attempts QUIC to `relay.cdn.example:443` with ALPN `moq-00`
3. Both → send MOQT SUBSCRIBE for namespace `["acme.com", "live", "sports"]`, track `catalog`

### Advantages of `moq://`

1. **Shorter URLs**: Every character matters in QR codes and deep links
2. **Clean Abstraction**: Transport is an implementation detail, not a URL concern
3. **Future-Proof**: New transports (WebTransport over HTTP/2, etc.) don't require scheme changes
4. **Standards-Aligned**: Follows RFC 3986 hierarchical URI model precisely
5. **Precedent**: Similar to how `mailto:` abstracts SMTP vs submission protocols

### Disadvantages of `moq://`

1. **Registration Required**: IANA process takes time
2. **Browser Integration**: Browsers need explicit `moq://` → `https://` conversion logic
3. **Debugging Complexity**: Transport not visible in URL makes debugging harder
4. **Potential Conflicts**: If MOQT and MSF diverge, single scheme may be insufficient

---

## Additional Proposal B: Well-Known URI Discovery Model

This proposal takes a fundamentally different approach: instead of encoding everything in a single URL, use a discovery mechanism based on the `.well-known` URI pattern established by RFC 8615.

### Core Concept

Separate the concerns into two phases:
1. **Discovery URL**: A standard HTTPS URL pointing to a discovery document
2. **Playback Descriptor**: A JSON document describing connection and subscription details

```
┌────────────────────────────────────────────────────────────────┐
│ User receives link: https://example.com/watch/sports-game-123  │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ Client fetches: GET https://example.com/watch/sports-game-123  │
│                 Accept: application/moqt+json                  │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ Server returns MOQT Playback Descriptor (JSON):                │
│ {                                                              │
│   "version": 1,                                                │
│   "endpoints": [                                               │
│     {                                                          │
│       "uri": "https://relay1.example.com/app",                 │
│       "transport": "webtransport",                             │
│       "priority": 1                                            │
│     },                                                         │
│     {                                                          │
│       "uri": "quic://relay2.example.com:4433/app",             │
│       "transport": "quic",                                     │
│       "priority": 2                                            │
│     }                                                          │
│   ],                                                           │
│   "subscription": {                                            │
│     "namespace": ["example.com", "live", "sports-game-123"],   │
│     "track": "catalog"                                         │
│   },                                                           │
│   "auth": {                                                    │
│     "tokens": ["eyJhbGciOiJFUzI1NiJ9..."]                      │
│   },                                                           │
│   "location": {                                                │
│     "start": { "group": 1000, "object": 0 },                   │
│     "end": { "group": 2000, "object": 15 }                     │
│   }                                                            │
│ }                                                              │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ Client connects to preferred endpoint and subscribes           │
└────────────────────────────────────────────────────────────────┘
```

### MOQT Playback Descriptor Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["version", "endpoints", "subscription"],
  "properties": {
    "version": {
      "type": "integer",
      "const": 1
    },
    "endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["uri", "transport"],
        "properties": {
          "uri": { "type": "string", "format": "uri" },
          "transport": { "enum": ["webtransport", "quic", "webtransport-h2"] },
          "priority": { "type": "integer", "minimum": 1 },
          "region": { "type": "string" }
        }
      }
    },
    "subscription": {
      "type": "object",
      "required": ["namespace", "track"],
      "properties": {
        "namespace": {
          "type": "array",
          "items": { "type": "string" }
        },
        "track": { "type": "string" }
      }
    },
    "auth": {
      "type": "object",
      "properties": {
        "tokens": {
          "type": "array",
          "items": { "type": "string" }
        },
        "refresh_url": { "type": "string", "format": "uri" }
      }
    },
    "location": {
      "type": "object",
      "properties": {
        "start": {
          "type": "object",
          "properties": {
            "group": { "type": "integer" },
            "object": { "type": "integer", "default": 0 }
          }
        },
        "end": {
          "type": "object",
          "properties": {
            "group": { "type": "integer" },
            "object": { "type": "integer" }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "duration": { "type": "number" },
        "poster": { "type": "string", "format": "uri" }
      }
    }
  }
}
```

### Alternative: Well-Known Endpoint

For cases where the discovery URL isn't the content URL:

```
# Content identifier
https://example.com/content/sports-game-123

# Discovery endpoint (well-known)
GET https://example.com/.well-known/moqt?content=/content/sports-game-123
Accept: application/moqt+json
```

This follows RFC 8615 patterns used by:
- `/.well-known/webfinger` (RFC 7033)
- `/.well-known/acme-challenge` (RFC 8555)
- `/.well-known/openid-configuration` (OpenID Connect)

### Content Negotiation Model

The same URL can serve different purposes based on `Accept` header:

| Accept Header | Response |
|---------------|----------|
| `text/html` | Web player page with embedded player |
| `application/moqt+json` | MOQT Playback Descriptor |
| `application/json` | Generic API response |

Example web page with embedded descriptor:

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="alternate" type="application/moqt+json"
        href="https://example.com/watch/sports-game-123">
  <script type="application/moqt+json" id="moqt-descriptor">
    {
      "version": 1,
      "endpoints": [...],
      "subscription": {...}
    }
  </script>
</head>
<body>
  <moqt-player src="#moqt-descriptor"></moqt-player>
</body>
</html>
```

### Advantages of Discovery Model

**1. No Escaping Complexity**

Namespace and track are native JSON arrays/strings:
```json
{
  "namespace": ["customer-123", "live/sports", "game--2024"],
  "track": "video"
}
```

No URL escaping needed. Hyphens, slashes, any characters work naturally.

**2. Rich Metadata Support**

The descriptor can include arbitrary metadata without URL length limits:
```json
{
  "subscription": {...},
  "metadata": {
    "title": "Championship Game 2024",
    "poster": "https://cdn.example.com/poster.jpg",
    "duration": 7200,
    "captions": ["en", "es", "fr"]
  }
}
```

**3. Multiple Endpoints with Failover**

```json
{
  "endpoints": [
    { "uri": "https://edge1.cdn.example/app", "priority": 1, "region": "us-west" },
    { "uri": "https://edge2.cdn.example/app", "priority": 1, "region": "us-east" },
    { "uri": "https://origin.example/app", "priority": 2 }
  ]
}
```

Clients can:
- Choose closest endpoint by region
- Implement automatic failover
- Load balance across priority-1 endpoints

**4. Token Refresh Without URL Change**

```json
{
  "auth": {
    "tokens": ["short-lived-token"],
    "refresh_url": "https://auth.example.com/refresh?session=abc123"
  }
}
```

Long-lived sessions can refresh tokens without generating new URLs.

**5. Versioning and Evolution**

New fields can be added without breaking existing clients:
```json
{
  "version": 2,
  "subscription": {...},
  "drm": {
    "system": "widevine",
    "license_url": "https://drm.example.com/license"
  }
}
```

**6. Shareable Human-Friendly URLs**

URLs shared socially are clean and memorable:
```
https://example.com/watch/championship-2024
```

Instead of:
```
moqt://relay.example.com:4433/app?c4m=eyJ...#example.com%2Flive%2Fchampionship%2D2024--catalog
```

### Disadvantages of Discovery Model

**1. Extra Round Trip**

Requires HTTP fetch before MOQT connection:
```
Client → HTTP GET → Server → MOQT Descriptor → Client → QUIC/WT → Server
```

Mitigation: HTTP/3 0-RTT or cached descriptors can reduce latency.

**2. Not Self-Contained**

The URL alone doesn't contain all information. Sharing a URL requires the server to be available.

Mitigation: For offline sharing, use inline descriptor:
```
data:application/moqt+json;base64,eyJ2ZXJzaW9uIjoxLC...
```

**3. Discovery Server Dependency**

If `example.com` is down, even if relay servers are up, playback fails.

Mitigation: DNS-based discovery as fallback (similar to SRV records).

**4. Caching Complexity**

Dynamic descriptors (personalized tokens) cannot be cached:
```
Cache-Control: private, no-cache
```

Static content can use:
```
Cache-Control: public, max-age=300
```

### Hybrid Approach: URL + Discovery

Combine direct URL with optional discovery:

```
moqt://relay.example.com/app#ns/broadcast--video?discover=https://example.com/watch/123
```

- Direct connection possible with URL alone
- `discover` parameter points to richer descriptor
- Clients can choose based on capability

### Comparison Matrix

| Criterion | Fragment-Based (PR #87) | Single Scheme (`moq://`) | Discovery Model |
|-----------|------------------------|--------------------------|-----------------|
| Self-contained | ✅ Yes | ✅ Yes | ❌ Requires fetch |
| Human-readable | ⚠️ With escaping | ⚠️ With escaping | ✅ Clean URLs |
| Escaping complexity | High | Medium | None |
| Multiple endpoints | ❌ No | ❌ No | ✅ Yes |
| Metadata support | ❌ Limited | ❌ Limited | ✅ Unlimited |
| Token refresh | ❌ New URL needed | ❌ New URL needed | ✅ In-band |
| Latency | ✅ Direct connect | ✅ Direct connect | ⚠️ Extra RTT |
| Offline sharing | ✅ URL sufficient | ✅ URL sufficient | ⚠️ Needs server |
| Standards compliance | ✅ RFC 3986 | ✅ RFC 3986 | ✅ RFC 8615 |
| Browser integration | ⚠️ Scheme handling | ⚠️ Scheme handling | ✅ Native HTTPS |

### Recommendation

The discovery model works best for:
- **Consumer-facing applications**: Clean URLs for social sharing
- **Multi-CDN deployments**: Endpoint selection and failover
- **DRM-protected content**: Rich auth and license integration
- **Long-form VOD**: Where extra RTT is negligible

The fragment-based approach works best for:
- **Low-latency live**: Every millisecond matters
- **Embedded systems**: Minimal HTTP stack
- **P2P scenarios**: Direct peer-to-peer URL exchange
- **Debugging**: Self-contained URLs for testing

A hybrid specification supporting both patterns would maximize flexibility.

---

## Additional Proposal C: Agent Discovery and MCP Integration

This proposal extends the Well-Known URI Discovery Model (Proposal B) to support AI agents, automated systems, and Model Context Protocol (MCP) integration.

### Motivation

MSF's Event Timeline and Media Timeline tracks already provide structured JSON data with time synchronization. This makes MOQT streams inherently valuable for:

- AI agents processing real-time events (sports scores, telemetry)
- Automated monitoring and alerting systems
- Computer vision pipelines consuming video frames
- Accessibility tools processing captions
- Analytics systems aggregating stream metadata

A standardized discovery mechanism would allow these systems to find and consume MOQT data programmatically.

### Extending the Playback Descriptor Schema

Building on Proposal B's MOQT Playback Descriptor, add an optional `agent_discovery` field:

```json
{
  "version": 1,
  "endpoints": [
    {
      "uri": "https://relay1.example.com/app",
      "transport": "webtransport",
      "priority": 1
    }
  ],
  "subscription": {
    "namespace": ["example.com", "live", "sports-game-123"],
    "track": "catalog"
  },
  "auth": {
    "tokens": ["eyJhbGciOiJFUzI1NiJ9..."]
  },

  "agent_discovery": {
    "description": "Live sports stream with real-time event data",
    "machine_readable_tracks": [
      {
        "role": "eventtimeline",
        "format": "application/json",
        "schema_url": "https://example.com/schemas/sports-events.json",
        "description": "Time-synced scores, fouls, substitutions, cards"
      },
      {
        "role": "mediatimeline",
        "format": "application/json",
        "description": "PTS-to-wallclock mapping for temporal navigation"
      },
      {
        "role": "caption",
        "format": "text/vtt",
        "lang": ["en", "es"],
        "description": "Live captions in WebVTT format"
      }
    ],
    "use_cases": [
      "real-time sports analysis",
      "automated highlight generation",
      "accessibility transcription",
      "betting odds correlation"
    ],
    "rate_limits": {
      "requests_per_minute": 60,
      "concurrent_subscriptions": 5
    },
    "mcp_server": "https://example.com/mcp/moqt-streams"
  }
}
```

### JSON Schema Extension

Add to Proposal B's schema (lines 767-839):

```json
{
  "agent_discovery": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "Human/agent readable description of the stream content"
      },
      "machine_readable_tracks": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["role", "format"],
          "properties": {
            "role": {
              "enum": ["eventtimeline", "mediatimeline", "caption", "subtitle", "data"]
            },
            "format": {
              "type": "string",
              "description": "MIME type of track content"
            },
            "schema_url": {
              "type": "string",
              "format": "uri",
              "description": "JSON Schema URL for structured data tracks"
            },
            "lang": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Available languages (BCP 47 tags)"
            },
            "description": {
              "type": "string"
            }
          }
        }
      },
      "use_cases": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Suggested applications for agent consumption"
      },
      "rate_limits": {
        "type": "object",
        "properties": {
          "requests_per_minute": { "type": "integer" },
          "concurrent_subscriptions": { "type": "integer" }
        }
      },
      "mcp_server": {
        "type": "string",
        "format": "uri",
        "description": "MCP server endpoint for tool-based access"
      }
    }
  }
}
```

### Integration with `/.well-known/agents.md`

For sites implementing an agent discovery convention (similar to `robots.txt` or ChatGPT's `ai-plugin.json`), MOQT capabilities can be referenced:

```markdown
# /.well-known/agents.md

## Available Data Sources

### MOQT Streaming Data
- **Discovery Endpoint**: `/.well-known/moqt?content={path}`
- **Protocol**: Media over QUIC Transport (MOQT)
- **Authentication**: Bearer tokens via `c4m` parameter

### Available Track Types

| Track Role | Format | Description |
|------------|--------|-------------|
| `eventtimeline` | `application/json` | Time-synchronized event data |
| `mediatimeline` | `application/json` | PTS/wallclock/group mapping |
| `caption` | `text/vtt` | WebVTT captions |
| `catalog` | `application/json` | Stream metadata and track list |

### Agent Workflow

1. **Discover**: `GET /.well-known/moqt?content=/live/game-123`
2. **Parse**: Extract `subscription.namespace` and `endpoints`
3. **Connect**: Establish WebTransport to `endpoints[0].uri`
4. **Subscribe**: Send MOQT SUBSCRIBE for desired track
5. **Consume**: Process objects as JSON/VTT/media

### Structured Data Example

Event Timeline objects contain JSON arrays:
\`\`\`json
[
  {"t": 1705500000000, "event": "goal", "team": "home", "player": "Smith"},
  {"t": 1705500045000, "event": "card", "type": "yellow", "player": "Jones"}
]
\`\`\`

### Rate Limits
- Discovery requests: 60/minute
- Concurrent subscriptions: 5 per token
- Contact: api-support@example.com
```

### MCP Server Integration

For Model Context Protocol integration, define MOQT-specific tools:

```json
{
  "name": "moqt-streams",
  "version": "1.0.0",
  "description": "Access MOQT streaming data",
  "tools": [
    {
      "name": "discover_stream",
      "description": "Get MOQT playback descriptor for a content path",
      "inputSchema": {
        "type": "object",
        "properties": {
          "content_path": {
            "type": "string",
            "description": "Content identifier (e.g., /live/game-123)"
          }
        },
        "required": ["content_path"]
      }
    },
    {
      "name": "get_catalog",
      "description": "Retrieve the catalog for a MOQT stream",
      "inputSchema": {
        "type": "object",
        "properties": {
          "namespace": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "required": ["namespace"]
      }
    },
    {
      "name": "query_events",
      "description": "Query event timeline data within a time range",
      "inputSchema": {
        "type": "object",
        "properties": {
          "namespace": {
            "type": "array",
            "items": { "type": "string" }
          },
          "start_time": {
            "type": "integer",
            "description": "Start wallclock time (ms since epoch)"
          },
          "end_time": {
            "type": "integer",
            "description": "End wallclock time (ms since epoch)"
          },
          "event_types": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Filter by event type (e.g., ['goal', 'card'])"
          }
        },
        "required": ["namespace"]
      }
    },
    {
      "name": "get_media_position",
      "description": "Map between wallclock time and media position",
      "inputSchema": {
        "type": "object",
        "properties": {
          "namespace": {
            "type": "array",
            "items": { "type": "string" }
          },
          "wallclock_time": {
            "type": "integer",
            "description": "Wallclock time to map"
          }
        },
        "required": ["namespace", "wallclock_time"]
      }
    }
  ]
}
```

### Agent Workflow Example

**Scenario**: AI agent answering "What happened in the 45th minute of the game?"

```
┌─────────────────────────────────────────────────────────────────┐
│ User Query: "What happened in the 45th minute of the game?"     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Agent discovers stream                                   │
│   GET /.well-known/moqt?content=/live/championship-2024          │
│   → Returns playback descriptor with agent_discovery metadata    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Agent identifies eventtimeline track                     │
│   machine_readable_tracks[0].role == "eventtimeline"             │
│   schema_url → understands event structure                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Agent queries via MCP or direct subscription             │
│   MCP: query_events(namespace, start=45*60*1000, end=46*60*1000) │
│   Direct: Subscribe to eventtimeline, filter by media_pts        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Agent processes structured event data                    │
│   Events: [                                                      │
│     {"m": 2700000, "event": "goal", "team": "home", ...},        │
│     {"m": 2723000, "event": "celebration", ...}                  │
│   ]                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent Response: "At 45:00, the home team scored a goal.          │
│ The scorer celebrated with teammates until 45:23."               │
└─────────────────────────────────────────────────────────────────┘
```

### Why MSF Tracks Are Agent-Friendly

| MSF Track Type | Agent Value |
|----------------|-------------|
| **Catalog** | Programmatic discovery of all available tracks, qualities, languages |
| **Event Timeline** | Structured JSON with indexed time references - ideal for queries |
| **Media Timeline** | Temporal navigation without video parsing |
| **Captions (WebVTT)** | Text extraction without speech recognition |
| **LOC video** | Frame-accurate access for computer vision |

The Event Timeline format (from MSF spec) is particularly valuable:

```json
[
  ["t", 1705500000000],
  ["l", [37.7749, -122.4194]],
  ["m", 2700000],
  {"event": "checkpoint", "data": {...}}
]
```

- `t` = wallclock timestamp (agent can correlate with real-world time)
- `l` = location (GPS for drone/vehicle streams)
- `m` = media PTS (sync with video frames)
- Arbitrary JSON payload for domain-specific data

### Advantages of Agent Discovery Extension

**1. Leverages Existing MSF Features**

No new track types needed. Event Timeline and Media Timeline already provide structured data; this proposal just makes them discoverable.

**2. Non-Breaking Extension**

The `agent_discovery` field is optional. Players that don't understand it simply ignore it:

```json
{
  "version": 1,
  "endpoints": [...],
  "subscription": {...},
  "agent_discovery": {...}  // Ignored by legacy players
}
```

**3. Schema-Driven Validation**

`schema_url` allows agents to validate event structures:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "event": { "enum": ["goal", "card", "substitution", "whistle"] },
    "team": { "enum": ["home", "away"] },
    "player": { "type": "string" },
    "minute": { "type": "integer" }
  }
}
```

**4. Rate Limiting Transparency**

Agents can respect published limits without trial-and-error:

```json
"rate_limits": {
  "requests_per_minute": 60,
  "concurrent_subscriptions": 5
}
```

**5. MCP Standardization**

As MCP adoption grows, having a standard MOQT server definition enables:
- IDE integrations (Claude Code, Cursor, etc.)
- Automated workflows (n8n, Zapier with AI)
- Custom agent frameworks

### Disadvantages and Concerns

**1. Scope Creep**

MSF is a media format specification. Adding agent discovery may exceed its intended scope.

*Mitigation*: Define as a separate "MSF Agent Discovery Extension" document that references MSF.

**2. Security Surface**

Exposing structured data to automated systems increases attack surface:
- Token leakage to malicious "agents"
- Resource exhaustion from aggressive crawlers
- Data scraping at scale

*Mitigation*:
- Require authentication for `agent_discovery` endpoints
- Rate limiting is part of the schema
- `robots.txt` style opt-out: `User-agent: * Disallow: /.well-known/moqt`

**3. Schema Maintenance Burden**

Publishers must maintain JSON schemas for event data.

*Mitigation*: Define common schemas for popular use cases (sports, telemetry, captions) that publishers can reference.

**4. MCP Immaturity**

Model Context Protocol is still evolving. Standardizing on it now may require future changes.

*Mitigation*: Make `mcp_server` optional; core discovery works without it.

### Comparison with Other Proposals

| Criterion | PR #87 | Proposal A | Proposal B | Proposal C (This) |
|-----------|--------|------------|------------|-------------------|
| Human players | ✅ | ✅ | ✅ | ✅ |
| AI agents | ❌ | ❌ | ⚠️ Basic | ✅ Native support |
| Structured data discovery | ❌ | ❌ | ❌ | ✅ Schema URLs |
| MCP integration | ❌ | ❌ | ❌ | ✅ Tool definitions |
| Rate limit communication | ❌ | ❌ | ❌ | ✅ In schema |
| Backward compatible | N/A | N/A | N/A | ✅ Optional fields |

### Implementation Phases

**Phase 1: Core Discovery**
- Implement Proposal B's `/.well-known/moqt` endpoint
- Return basic playback descriptors

**Phase 2: Agent Metadata**
- Add optional `agent_discovery` field
- Document machine-readable track types
- Publish common event schemas

**Phase 3: MCP Integration**
- Define standard MOQT MCP server specification
- Implement reference server
- Register with MCP tool directories

### Conclusion

MSF's existing Event Timeline and Media Timeline tracks provide structured, time-synchronized data that is immediately valuable to AI agents and automated systems. The Well-Known URI Discovery Model (Proposal B) offers a natural extension point for agent-specific metadata.

Adding `agent_discovery` as an optional field:
- Requires no changes to core MSF
- Enables programmatic discovery of structured data tracks
- Provides schema URLs for data validation
- Communicates rate limits transparently
- Optionally integrates with MCP for tool-based access

This positions MOQT/MSF for the emerging ecosystem of AI agents that can consume and reason about real-time streaming data.

---

## References

- [Issue #60: URL syntax identifying both connection and track](https://github.com/moq-wg/msf/issues/60)
- [PR #72: Query parameter approach](https://github.com/moq-wg/msf/pull/72)
- [PR #87: Fragment-based approach](https://github.com/moq-wg/msf/pull/87)
- [Issue #65: Access token passing](https://github.com/moq-wg/msf/issues/65)
- [moq-transport#1355: Name formatting for logs](https://github.com/moq-wg/moq-transport/pull/1355)
- [RFC 3986: URI Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [RFC 7595: Guidelines and Registration Procedures for URI Schemes](https://www.rfc-editor.org/rfc/rfc7595)
- [RFC 8615: Well-Known URIs](https://www.rfc-editor.org/rfc/rfc8615)
