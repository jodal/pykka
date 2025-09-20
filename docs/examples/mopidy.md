# Mopidy music server

Pykka was originally created around 2011 as
a formalization of concurrency patterns that emerged in
the [Mopidy music server](https://www.mopidy.com/).
The original Pykka source code wasn't extracted from Mopidy,
but it built and improved on the concepts from Mopidy.
Mopidy was later ported to build on Pykka
instead of its own concurrency abstractions.

Mopidy still use Pykka extensively to keep independent parts,
like the MPD and HTTP servers
or the Spotify and Youtube Music integrations,
running independently.
Every one of Mopidy's more than 100 extensions has at least one Pykka actor.
By running each extension as an independent actor,
errors and bugs in one extension is attempted isolated,
to reduce the effect on the rest of the system.

You can browse the
[Mopidy source code](https://github.com/mopidy/mopidy)
to find many real life examples of Pykka usage.
