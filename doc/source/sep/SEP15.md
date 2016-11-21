	Title: Moving Sardana to Github
	SEP: 15
	State: DRAFT
	Date: 2016-11-21
	Drivers: Marc Rosanes <mrosanes@cells.es>, Zbigniew Reszela <zreszela@cells.es>
	URL: https://sourceforge.net/p/sardana/wiki/SEP15
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	 Move Sardana project from its current hosting in SourceForge to 
	 GitHub. The move affects the code repository, the ticket tracker and the 
	 wiki pages. It also proposes to change the contribution and the SEP 
	 workflow to make use of the Pull Request feature.



 
## Introduction

SEP15 is for Sardana what [TEP16][] is for Taurus.
SEP15 proposes the migration of the Sardana project from its current hosting in SourceForge (SF) to the GitHub (GH) service, and to change the contribution workflow (defined in SEP7) to one based on Pull Requests (PR).

The following reasons are considered in favour of migrating to GH:

- It would alleviate the current saturation of the -devel mailing list (since the code review would be done via PR)
- A PR-based workflow for contributions is preferred by all the integrators and most of the current contributors and is expected to attract more new contributors
- It would enable the use of Travis for public Continuous Integration and Deployment
- GH is perceived as more user friendly than SF
- GH is perceived as providing more visibility than SF
- Tango (with which we share a lot of developers and users) is currently doing a similar transition.
- Most developers already have an account in GH

The following reasons were considered against migrating to GH:

- GH is a closed-source product (which may raise ethic concerns and increase the risk of lock-in). Gitlab would be preferred in this particular aspect.



## Changes

- 2016-11-21 [mrosanes][]. Initial version



[TEP16]: http://www.taurus-scada.org/tep/?TEP16.md

[mrosanes]: https://github.com/sagiss/
