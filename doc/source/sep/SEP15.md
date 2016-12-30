	Title: Moving Sardana to Github
	SEP: 15
	State: ACCEPTED
	Date: 2016-11-21
	Drivers: Marc Rosanes <mrosanes@cells.es>, Zbigniew Reszela <zreszela@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP15.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	 Move Sardana project from its current hosting in SourceForge to 
	 GitHub. The move affects the code repository, the ticket tracker and the 
	 wiki pages. It also proposes to change the contribution and the SEP 
	 workflow to make use of the Pull Request feature.

## Introduction

SEP15 is for Sardana what [TEP16][] is for Taurus.
SEP15 proposes the migration of the Sardana project from its current hosting in 
SourceForge (SF) to the GitHub (GH) service, and to change the contribution 
workflow (defined in SEP7) to one based on Pull Requests (PR).

The following reasons are considered in favour of migrating to GH:

- It would alleviate the current saturation of the devel mailing list (since 
the code review would be done via PR)
- A PR-based workflow for contributions is preferred by all the integrators and 
most of the current contributors and is expected to attract more new 
contributors
- It would enable the use of Travis for public Continuous Integration and 
Deployment
- GH is perceived as more user friendly than SF
- GH is perceived as providing more visibility than SF
- Tango (with which we share a lot of developers and users) is currently doing 
a similar transition.
- Most developers already have an account in GH

The following reasons were considered against migrating to GH:

- GH is a closed-source product (which may raise ethic concerns and increase 
the risk of lock-in). Gitlab would be preferred in this particular aspect.

## Relationship with other Enhancement Proposals

This SEP obsoletes totally or partially some previous Enhancement Proposals (EP), 
as summarized here:

- SEP0: `https://sourceforge.net/p/sardana/wiki/SEP/` is no longer the index for 
SEPs. The index for the SEPs is now located at http://www.sardana-controls.org/sep/. The "Creating a SEP" of SEP0 is superseded by the section "Creating a SEP: New policy for SEPs" of SEP15.
- SEP1: references to SF
- SEP7: most of the contribution procedure is no longer applicable due to 
the adoption of PR-based workflow.
- SEP10: references to SF

This Enhancement proposal is done after the implementation of TEP16, which is 
the counterpart of this SEP for Taurus. 
TEP16 is already in ACCEPTED state at the creation of this SEP.

## Goals

The goals are roughly described in order of priority:

1. Create a sardana repo within a Sardana GH organization
2. Define the new contribution policy
3. Define the policy for bug reports / feature requests
4. Migrate SF tickets to GH Issues
5. Move the SEP pages to a service-independent URL
6. Define what to do with the mailing lists

## Implementation

The implementation steps to accomplish each of the goals are listed below:

### New sardana repo within a Sardana GH organization

- A GH organization called sardana-org will be created

- A sardana project will be created within sardana-org and the current master 
and develop branches pushed to it

- The Travis continuous integration services will be enabled for this repo.

- The third party controllers and macros repositories will stay in SourceForge
until further notice.

### New contribution policy

- The new contribution policy will be detailed in the CONTRIBUTING.md file at 
the root of the repository. It should be based on Pull Requests instead of the 
current email-based policy described in SEP7.

### New policy for bug reports and feature requests

- Bugs and feature requests will be reported via [GitHub Issues][] instead of 
using SF tickets.

### Migration of SF tickets to GH Issues

- Existing tickets in the ticket tracker for the sardana project in SF will be 
migrated using the same tools and procedure described for migrating the tickets 
of the Tango projects. To this purpose, some tools from 
https://github.com/taurus-org/svn2git-migration will be used.

- The SF ticket tracker will be locked to prevent further ticket creation, 
and its SF tool menu entry will be renamed to "Old Tickets". A new SF tool 
menu entry called "Tickets" will be added pointing to the new 
sardana GH issues URL

- Prominent notices will be added in the SF ticket tracker indicating that 
the new GH tracker should be used instead.

### Creating a SEP: New policy for SEPs

- All SEPs will be stored as files in `<new_sep_location>` in the repository.
We propose `<new_sep_location>` to be defined as `doc/source/sep`.

- To start a new SEP, the SEP driver submits a PR containing, at least, 
one file called `<new_sep_location>/SEPX[.md|.txt|.rst|...]`, where X is 
the SEP number and the extension depends on the the markup language 
used (as of today, we recommend `.md`).

- The discussion for this new SEP should take place using the comments and 
similar tools within the PR itself.

- If the SEP includes some proposal of implementation in the form of code, 
the changes should be committed as part of the same PR (and reviewed with it).

- If the SEP reaches the ACCEPTED stage, the PR is merged (which, at 
the same time, will bring the source code implementation changes, if any). 
If the SEP is REJECTED, the integrator will issue a commit in the PR reverting 
any implementation changes (if any) and then he/she will merge the PR so that 
the whole discussion history is not lost.

### Migration of existing SEP pages and index

- A file called `<new_sep_location>/SEPX.md` will be created for 
each existing SEP (X being the SEP number).

- A file called `index.md` will be created in `<new_sep_location>`, containing 
the info currently in `https://sourceforge.net/p/sardana/wiki/SEP`. The 
provisions in SEP0 for that page now apply to `index.md` (i.e., 
**SEP drivers are required to update the status of their SEP in this page**).

- Service-provider independent URLs will be configured to redirect to the new 
location of the SEPs and the index. This service-agnostic URLs should be used 
instead of the SF or GH specific location in all documentation from now on 
(this allows us to change the location in the future without altering the docs). 
In the proposed implementation, these URLs are:
    - `http://www.sardana-controls.org/sep/` (for the SEP index)
    - `http://www.sardana-controls.org/sep/?<SEP_FILE_NAME>` (e.g., for SEP15, 
this agnostic URL would be http://www.sardana-controls.org/sep/?SEP15.md)

- The wiki pages served under `https://sourceforge.net/p/sardana/wiki/SEP/` 
should redirect to the new location.

### Mailing lists

GH does not provide mailing list hosting. For now, continue using 
the existing mailing lists provided by SF. 

## Links to more details and discussions

Discussions for this SEP are conducted in its associated Pull Request: 
https://github.com/sardana-org/sardana/pull/1

## License

Copyright (c) 2016 Marc Rosanes Siscart

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Changes

- 2016-11-21 [mrosanes][]. Initial version
- 2016-11-30 [reszelaz][]. DRAFT -> CANDIDATE (review & minor corrections)
- 2016-12-01 [reszelaz][]. CANDIDATE -> ACCEPTED


[TEP16]: http://www.taurus-scada.org/tep/?TEP16.md
[GitHub Issues]: https://guides.github.com/features/issues/
[mrosanes]: https://github.com/sagiss/
[reszelaz]: https://github.com/reszelaz
