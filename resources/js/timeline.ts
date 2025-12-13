/**
 * Python Timeline - Interactive River Flow Component
 *
 * Features:
 * - Scroll-triggered animations using Intersection Observer
 * - Expandable event details
 * - Filtering by event type
 * - Search functionality
 * - Progress indicator
 * - Keyboard navigation
 */

interface TimelineEvent {
  id: string;
  year: number;
  month?: string;
  title: string;
  description: string;
  type: 'release' | 'pep' | 'event' | 'milestone';
  details?: string;
  highlights?: string[];
  pepNumber?: number;
  version?: string;
  links?: { label: string; url: string }[];
}

// Timeline Alpine.js Component
document.addEventListener('alpine:init', () => {
  window.Alpine.data('pythonTimeline', () => ({
    events: [] as TimelineEvent[],
    filteredEvents: [] as TimelineEvent[],
    activeFilter: 'all',
    searchQuery: '',
    expandedEvents: new Set<string>(),
    visibleEvents: new Set<string>(),
    currentEra: '',
    showProgress: false,

    init() {
      this.events = this.getTimelineData();
      this.filteredEvents = [...this.events];
      this.setupIntersectionObserver();
      this.setupScrollProgress();
      this.setupKeyboardNav();
    },

    getTimelineData(): TimelineEvent[] {
      return [
        // Origins Era (1989-1994)
        {
          id: 'conception',
          year: 1989,
          month: 'Dec',
          title: 'Python Conceived',
          description: 'Guido van Rossum begins working on Python at CWI in the Netherlands as a successor to ABC.',
          type: 'milestone',
          details: 'Python was conceived during the Christmas holiday when Guido was looking for a hobby programming project. He wanted a scripting language that was more readable than Perl and more powerful than shell scripting.',
          highlights: ['ABC successor', 'Christmas project', 'CWI Netherlands']
        },
        {
          id: 'first-release',
          year: 1991,
          month: 'Feb',
          title: 'Python 0.9.0 Released',
          description: 'First public release of Python posted to alt.sources, featuring classes, exception handling, and core data types.',
          type: 'release',
          version: '0.9.0',
          details: 'This version already included classes with inheritance, exception handling, functions, and the core datatypes of list, dict, str, and others. It was posted to the alt.sources newsgroup.',
          highlights: ['Classes & inheritance', 'Exception handling', 'Core datatypes', 'alt.sources']
        },
        {
          id: 'python-1',
          year: 1994,
          month: 'Jan',
          title: 'Python 1.0 Released',
          description: 'First major release including lambda, map, filter, and reduce - functional programming features.',
          type: 'release',
          version: '1.0',
          details: 'Python 1.0 introduced functional programming tools inspired by Lisp, making Python more versatile for different programming paradigms.',
          highlights: ['Functional programming', 'lambda expressions', 'map/filter/reduce']
        },

        // Growth Era (1995-2000)
        {
          id: 'python-1.5',
          year: 1998,
          month: 'Jan',
          title: 'Python 1.5 Released',
          description: 'Major improvements including better string methods, Unicode support preparation, and package imports.',
          type: 'release',
          version: '1.5',
          highlights: ['Package imports', 'String methods', 'Unicode prep']
        },
        {
          id: 'pep-process',
          year: 2000,
          month: 'Jul',
          title: 'PEP Process Established',
          description: 'Python Enhancement Proposal (PEP) process introduced to formalize language development.',
          type: 'pep',
          pepNumber: 1,
          details: 'The PEP process was inspired by RFCs and provides a consistent way to propose and track changes to Python. It has become a model for other programming languages.',
          highlights: ['Formalized development', 'Community input', 'Transparency']
        },
        {
          id: 'python-2',
          year: 2000,
          month: 'Oct',
          title: 'Python 2.0 Released',
          description: 'Revolutionary release with list comprehensions, garbage collection, and Unicode support.',
          type: 'release',
          version: '2.0',
          details: 'Python 2.0 was the first release developed with community involvement via SourceForge. It introduced list comprehensions inspired by Haskell and proper Unicode support.',
          highlights: ['List comprehensions', 'Garbage collection', 'Unicode support', 'Community dev']
        },

        // PSF Era (2001-2008)
        {
          id: 'psf-formed',
          year: 2001,
          month: 'Mar',
          title: 'Python Software Foundation Formed',
          description: 'Non-profit organization created to hold Python intellectual property and promote the language.',
          type: 'event',
          details: 'The PSF was modeled after the Apache Software Foundation and ensures Python remains open source and freely available.',
          highlights: ['Non-profit', 'IP protection', 'Community support']
        },
        {
          id: 'pep-8',
          year: 2001,
          month: 'Jul',
          title: 'PEP 8 - Style Guide',
          description: 'The official Python style guide published, defining coding conventions still used today.',
          type: 'pep',
          pepNumber: 8,
          details: 'PEP 8 codified "Pythonic" style and remains the most referenced PEP. It emphasizes readability and consistency across Python codebases worldwide.',
          highlights: ['Code style', 'Readability first', 'Industry standard']
        },
        {
          id: 'pep-20',
          year: 2004,
          month: 'Aug',
          title: 'PEP 20 - The Zen of Python',
          description: 'Tim Peters writes the guiding principles for Python\'s design, accessible via "import this".',
          type: 'pep',
          pepNumber: 20,
          details: '"Beautiful is better than ugly. Explicit is better than implicit." These 19 aphorisms guide Python development philosophy.',
          highlights: ['Design philosophy', 'import this', '19 aphorisms']
        },
        {
          id: 'pep-318',
          year: 2004,
          month: 'Sep',
          title: 'PEP 318 - Decorators',
          description: 'Function and method decorators introduced with the @ syntax.',
          type: 'pep',
          pepNumber: 318,
          details: 'Decorators provide a clean syntax for modifying functions and methods, enabling frameworks like Flask and FastAPI.',
          highlights: ['@ syntax', 'Metaprogramming', 'Framework enabler']
        },
        {
          id: 'django',
          year: 2005,
          month: 'Jul',
          title: 'Django Framework Released',
          description: 'The web framework for perfectionists with deadlines goes open source.',
          type: 'event',
          details: 'Originally developed at World Online, Django popularized Python for web development and influenced countless frameworks.',
          highlights: ['Web framework', 'Batteries included', 'ORM']
        },
        {
          id: 'python-2.5',
          year: 2006,
          month: 'Sep',
          title: 'Python 2.5 Released',
          description: 'Introduced with statement, conditional expressions, and partial function application.',
          type: 'release',
          version: '2.5',
          highlights: ['with statement', 'Conditional expressions', 'functools']
        },
        {
          id: 'pep-3000',
          year: 2006,
          month: 'Apr',
          title: 'PEP 3000 - Python 3000',
          description: 'The plan for Python 3 announced, a backward-incompatible cleanup of the language.',
          type: 'pep',
          pepNumber: 3000,
          details: 'This PEP outlined the goals for Python 3: removing cruft, improving Unicode handling, and making the language more consistent.',
          highlights: ['Breaking changes', 'Unicode default', 'Language cleanup']
        },

        // Python 3 Era (2008-2015)
        {
          id: 'python-3',
          year: 2008,
          month: 'Dec',
          title: 'Python 3.0 Released',
          description: 'A major, backward-incompatible release focused on fixing fundamental design flaws.',
          type: 'release',
          version: '3.0',
          details: 'Python 3 made print a function, strings Unicode by default, and cleaned up many inconsistencies. It took years for the ecosystem to migrate.',
          highlights: ['print() function', 'Unicode strings', 'Integer division', 'Clean syntax']
        },
        {
          id: 'pip',
          year: 2011,
          month: 'Apr',
          title: 'pip Becomes Standard',
          description: 'pip officially recommended as the package installer, replacing easy_install.',
          type: 'event',
          details: 'pip (Pip Installs Packages) revolutionized Python package management with requirements.txt and virtual environment support.',
          highlights: ['Package management', 'requirements.txt', 'Virtual environments']
        },
        {
          id: 'pep-405',
          year: 2012,
          month: 'Jun',
          title: 'PEP 405 - venv Module',
          description: 'Built-in virtual environment support added to Python standard library.',
          type: 'pep',
          pepNumber: 405,
          details: 'The venv module made creating isolated Python environments a first-class feature, simplifying dependency management.',
          highlights: ['Built-in venvs', 'Isolation', 'No third-party needed']
        },
        {
          id: 'pep-484',
          year: 2014,
          month: 'Sep',
          title: 'PEP 484 - Type Hints',
          description: 'Optional type annotations introduced, enabling static type checking.',
          type: 'pep',
          pepNumber: 484,
          details: 'Type hints allow developers to annotate types without affecting runtime behavior, enabling tools like mypy for static analysis.',
          highlights: ['Static typing', 'Optional annotations', 'Tool support']
        },
        {
          id: 'python-3.5',
          year: 2015,
          month: 'Sep',
          title: 'Python 3.5 Released',
          description: 'Introduced async/await syntax, matrix multiplication operator, and type hints.',
          type: 'release',
          version: '3.5',
          details: 'The async/await syntax made asynchronous programming dramatically more readable and accessible to Python developers.',
          highlights: ['async/await', 'Matrix @', 'Type hints', 'Coroutines']
        },

        // Modern Era (2016-2020)
        {
          id: 'pep-557',
          year: 2017,
          month: 'Sep',
          title: 'PEP 557 - Data Classes',
          description: 'Data Classes decorator introduced for boilerplate-free class definitions.',
          type: 'pep',
          pepNumber: 557,
          details: 'Data classes automatically generate __init__, __repr__, and comparison methods, reducing boilerplate code significantly.',
          highlights: ['@dataclass', 'Auto-generated methods', 'Less boilerplate']
        },
        {
          id: 'python-3.7',
          year: 2018,
          month: 'Jun',
          title: 'Python 3.7 Released',
          description: 'Data classes, postponed evaluation of annotations, and breakpoint() built-in.',
          type: 'release',
          version: '3.7',
          highlights: ['Data classes', 'breakpoint()', 'Guaranteed dict order']
        },
        {
          id: 'guido-retirement',
          year: 2018,
          month: 'Jul',
          title: 'Guido Steps Down as BDFL',
          description: 'After PEP 572 controversy, Guido van Rossum retires as Benevolent Dictator For Life.',
          type: 'milestone',
          details: 'After 30 years of leading Python, Guido stepped down, leading to the establishment of the Steering Council governance model.',
          highlights: ['End of BDFL', 'PEP 572', 'New governance needed']
        },
        {
          id: 'pep-8016',
          year: 2018,
          month: 'Dec',
          title: 'PEP 8016 - Steering Council',
          description: 'New governance model adopted with a five-member elected Steering Council.',
          type: 'pep',
          pepNumber: 8016,
          details: 'The Steering Council consists of five elected members who make final decisions on PEPs and language direction.',
          highlights: ['5-member council', 'Democratic election', 'Community governance']
        },
        {
          id: 'python-3.8',
          year: 2019,
          month: 'Oct',
          title: 'Python 3.8 Released',
          description: 'Walrus operator (:=), positional-only parameters, and f-string debugging.',
          type: 'release',
          version: '3.8',
          details: 'The controversial walrus operator allows assignment expressions, enabling more concise code in certain patterns.',
          highlights: [':= operator', 'Positional-only params', 'f"{var=}"']
        },
        {
          id: 'python2-eol',
          year: 2020,
          month: 'Jan',
          title: 'Python 2 End of Life',
          description: 'After 20 years, Python 2 reaches end of life, concluding the migration period.',
          type: 'milestone',
          details: 'Python 2.7.18 was the final release. The 12+ year migration from Python 2 to 3 officially ended.',
          highlights: ['Final Python 2 release', '12-year migration', 'Python 3 only']
        },
        {
          id: 'python-3.9',
          year: 2020,
          month: 'Oct',
          title: 'Python 3.9 Released',
          description: 'Dictionary merge operators, type hinting generics, and new parser.',
          type: 'release',
          version: '3.9',
          highlights: ['Dict | merge', 'Generic types', 'PEG parser', 'Zone info']
        },

        // Current Era (2021-Present)
        {
          id: 'python-3.10',
          year: 2021,
          month: 'Oct',
          title: 'Python 3.10 Released',
          description: 'Structural pattern matching (match-case), better error messages, and parenthesized context managers.',
          type: 'release',
          version: '3.10',
          details: 'Pattern matching brings powerful switch-case-like syntax with destructuring capabilities.',
          highlights: ['match-case', 'Better errors', 'Union types X | Y']
        },
        {
          id: 'sc-election-2024',
          year: 2023,
          month: 'Dec',
          title: 'Steering Council Election (2024 Term)',
          description: 'First election after adopting new governance model continues.',
          type: 'event',
          details: 'Of 87 eligible voters, 68 cast ballots. Elected members: Pablo Galindo Salgado, Gregory P. Smith, Emily Morehouse, Barry Warsaw, Thomas Wouters.',
          highlights: ['68/87 voters', '5 members elected', 'Second full council term'],
          links: [{ label: 'PEP 8105', url: 'https://peps.python.org/pep-8105/' }]
        },
        {
          id: 'pep-703',
          year: 2023,
          month: 'Oct',
          title: 'PEP 703 - Optional GIL Accepted',
          description: 'Proposal to make the Global Interpreter Lock optional accepted by Steering Council.',
          type: 'pep',
          pepNumber: 703,
          details: 'The Steering Council accepted this historic PEP on October 24, 2023 with a gradual rollout plan. Introduces --disable-gil build flag for CPython to run without the GIL.',
          highlights: ['--disable-gil flag', 'Gradual rollout', 'Py_GIL_DISABLED macro']
        },
        {
          id: 'python-3.11',
          year: 2022,
          month: 'Oct',
          title: 'Python 3.11 Released',
          description: '10-60% faster execution, fine-grained error locations, and exception groups.',
          type: 'release',
          version: '3.11',
          details: 'Major performance improvements through the Faster CPython project made Python significantly more competitive.',
          highlights: ['10-60% faster', 'Exception groups', 'TOML support', 'Fine-grained errors']
        },
        {
          id: 'python-3.12',
          year: 2023,
          month: 'Oct',
          title: 'Python 3.12 Released',
          description: 'Per-interpreter GIL, improved f-strings, and type parameter syntax.',
          type: 'release',
          version: '3.12',
          details: 'Major step toward free-threaded Python with per-interpreter GIL, plus more flexible f-string syntax.',
          highlights: ['Per-interpreter GIL', 'F-string expressions', 'Type param syntax', 'Faster startup']
        },
        {
          id: 'python-3.13',
          year: 2024,
          month: 'Oct',
          title: 'Python 3.13 Released',
          description: 'Experimental free-threaded mode (no-GIL), JIT compiler, and improved REPL.',
          type: 'release',
          version: '3.13',
          details: 'Historic release with experimental no-GIL build and just-in-time compilation, marking a new era for Python performance.',
          highlights: ['Free-threaded (no-GIL)', 'JIT compiler', 'New REPL', 'iOS/Android support']
        },
        {
          id: 'core-sprint-2024',
          year: 2024,
          month: 'Sep',
          title: 'Core Dev Sprint 2024',
          description: 'Meta hosts 40+ core developers at Bellevue WA for intensive Python development.',
          type: 'event',
          details: 'A week at Meta\'s Spring District campus brought together core developers, triagers, and guests. Key topics: JIT compiler progress, type annotations in CPython, PEP 2026, and 5-year deprecation cycles. Python 3.13 release was delayed due to incremental GC issue discovered during the sprint.',
          highlights: ['40+ core devs', 'Meta Bellevue campus', 'JIT compiler updates', 'PEP 2026 submitted'],
          links: [{ label: 'Sprint Report', url: 'https://hugovk.dev/blog/2024/python-core-developer-sprint-2024/' }]
        },
        {
          id: 'sc-election-2025',
          year: 2024,
          month: 'Dec',
          title: 'Steering Council Election (2025 Term)',
          description: 'Donghee Na joins the Steering Council, replacing Thomas Wouters.',
          type: 'event',
          details: 'Of 100 eligible voters, 76 cast ballots. Elected members: Barry Warsaw, Donghee Na, Emily Morehouse, Gregory P. Smith, Pablo Galindo Salgado. Voting period: Nov 25 - Dec 9, 2024.',
          highlights: ['76/100 voters', 'Donghee Na elected', 'Thomas Wouters steps down'],
          links: [{ label: 'PEP 8106', url: 'https://peps.python.org/pep-8106/' }]
        },
        {
          id: 'pep-649',
          year: 2023,
          month: 'May',
          title: 'PEP 649 - Deferred Annotations (Final)',
          description: 'Deferred evaluation of annotations finalized, superseding PEP 563.',
          type: 'pep',
          pepNumber: 649,
          details: 'Annotations are now evaluated lazily via __annotate__ descriptor when accessed, not at binding time. This became the default in Python 3.14.',
          highlights: ['__annotate__ descriptor', 'Lazy evaluation', 'Supersedes PEP 563']
        },
        {
          id: 'pep-723-final',
          year: 2024,
          month: 'Jan',
          title: 'PEP 723 - Inline Script Metadata (Final)',
          description: 'Standard for embedding dependencies in single-file Python scripts finalized.',
          type: 'pep',
          pepNumber: 723,
          details: 'Enables tools like uv and pip to automatically install dependencies for standalone scripts. Canonical spec maintained by PyPA.',
          highlights: ['Script dependencies', 'uv/pip support', 'PyPA standard']
        },
        {
          id: 'python-3.14',
          year: 2025,
          month: 'Oct',
          title: 'Python 3.14 Released',
          description: 'Free-threaded Python official, PEP 649 default, template strings, colorful REPL, and major performance gains.',
          type: 'release',
          version: '3.14',
          details: 'Historic release: free-threaded Python (PEP 779) officially supported, deferred annotations default (PEP 649), t-strings (PEP 750), multiple interpreters (PEP 734), and 3-5% faster via tail-call interpreter. The REPL now features syntax highlighting with beautiful colors!',
          highlights: ['Free-threaded official', 'PEP 649 default', 'T-strings (PEP 750)', 'Zstd compression', 'Tail-call interpreter', '🌈 Colorful REPL'],
          specialHighlight: '🌈 Colorful REPL',
          links: [{ label: 'What\'s New', url: 'https://docs.python.org/3.14/whatsnew/3.14.html' }]
        },
        {
          id: 'python-3.9-eol',
          year: 2025,
          month: 'Oct',
          title: 'Python 3.9 End of Life',
          description: 'Python 3.9 reaches end of life after 5 years of support.',
          type: 'milestone',
          details: 'Python 3.9 officially reached EOL on October 31, 2025. Python 3.10 is now the oldest supported version (security fixes only until October 2026).',
          highlights: ['5-year lifecycle', 'Security-only since 2022', 'Upgrade to 3.10+']
        },
        {
          id: 'core-sprint-2025',
          year: 2025,
          month: 'Sep',
          title: 'Core Dev Sprint 2025',
          description: 'Arm Ltd hosts 35 core developers and 13 guests in Cambridge, UK.',
          type: 'event',
          details: 'A week at Arm headquarters featured mentorship discussions, Claude AI demos for CPython development, Python 3.14.0rc3 release during sprint, and social events including punting on the River Cam. Savannah Ostrowski shadowed as future release manager for 3.16/3.17.',
          highlights: ['35 core devs + 13 guests', 'Arm Cambridge HQ', 'Mentorship focus', 'AI tooling demos'],
          links: [{ label: 'Sprint Report', url: 'https://hugovk.dev/blog/2025/python-core-sprint/' }]
        },
        {
          id: 'psf-nsf-withdrawal',
          year: 2025,
          month: 'Oct',
          title: 'PSF Withdraws $1.5M NSF Grant',
          description: 'PSF unanimously votes to withdraw NSF grant over DEI policy conflict.',
          type: 'event',
          details: 'The PSF Board withdrew a recommended $1.5M NSF grant for Python/PyPI security improvements after grant terms required affirming no DEI programs, conflicting with PSF\'s mission to support a diverse international community.',
          highlights: ['$1.5M security grant', 'DEI policy conflict', 'Unanimous board vote'],
          links: [{ label: 'PSF Statement', url: 'https://pyfound.blogspot.com/2025/10/NSF-funding-statement.html' }]
        },
        {
          id: 'sc-election-2026',
          year: 2025,
          month: 'Dec',
          title: 'Steering Council Election (2026 Term)',
          description: 'Savannah Ostrowski joins, Thomas Wouters returns to the Steering Council.',
          type: 'event',
          details: 'Elected members: Pablo Galindo Salgado (313 votes), Savannah Ostrowski (249 votes), Barry Warsaw (239 votes), Donghee Na (191 votes), Thomas Wouters (187 votes). Emily Morehouse and Gregory P. Smith step down.',
          highlights: ['Savannah Ostrowski elected', 'Thomas Wouters returns', '5 members elected'],
          links: [{ label: 'PEP 8107', url: 'https://peps.python.org/pep-8107/' }]
        }
      ];
    },

    setupIntersectionObserver() {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            const eventId = entry.target.getAttribute('data-event-id');
            if (entry.isIntersecting) {
              entry.target.classList.add('visible');
              if (eventId) this.visibleEvents.add(eventId);
            }
          });
        },
        {
          threshold: 0.2,
          rootMargin: '0px 0px -10% 0px'
        }
      );

      this.$nextTick(() => {
        document.querySelectorAll('.timeline-event').forEach((el) => {
          observer.observe(el);
        });
      });
    },

    setupScrollProgress() {
      const timeline = document.querySelector('.timeline-river');
      if (!timeline) return;

      window.addEventListener('scroll', () => {
        const rect = timeline.getBoundingClientRect();
        const windowHeight = window.innerHeight;

        this.showProgress = rect.top < windowHeight && rect.bottom > 0;

        // Update current era based on scroll position - use lowercase to match getEraForYear()
        const events = document.querySelectorAll('.timeline-event');
        events.forEach((event) => {
          const eventRect = event.getBoundingClientRect();
          if (eventRect.top < windowHeight / 2 && eventRect.bottom > 0) {
            const year = event.getAttribute('data-year');
            if (year) {
              // Use same values as getEraForYear() for consistency
              if (parseInt(year) < 1995) this.currentEra = 'origins';
              else if (parseInt(year) < 2001) this.currentEra = 'growth';
              else if (parseInt(year) < 2009) this.currentEra = 'psf';
              else if (parseInt(year) < 2016) this.currentEra = 'python3';
              else if (parseInt(year) < 2021) this.currentEra = 'modern';
              else this.currentEra = 'current';
            }
          }
        });
      });
    },

    setupKeyboardNav() {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.expandedEvents.clear();
          this.$nextTick(() => this.updateExpandedClasses());
        }
      });
    },

    filterEvents(type: string) {
      this.activeFilter = type;
      if (type === 'all') {
        this.filteredEvents = [...this.events];
      } else {
        this.filteredEvents = this.events.filter((e) => e.type === type);
      }
    },

    searchEvents() {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) {
        this.filterEvents(this.activeFilter);
        return;
      }

      this.filteredEvents = this.events.filter((e) => {
        const matchesFilter = this.activeFilter === 'all' || e.type === this.activeFilter;
        const matchesSearch =
          e.title.toLowerCase().includes(query) ||
          e.description.toLowerCase().includes(query) ||
          e.year.toString().includes(query) ||
          (e.version && e.version.includes(query)) ||
          (e.pepNumber && `pep ${e.pepNumber}`.includes(query)) ||
          (e.highlights && e.highlights.some((h) => h.toLowerCase().includes(query)));
        return matchesFilter && matchesSearch;
      });
    },

    toggleExpand(eventId: string) {
      if (this.expandedEvents.has(eventId)) {
        this.expandedEvents.delete(eventId);
      } else {
        this.expandedEvents.add(eventId);
      }
      this.$nextTick(() => this.updateExpandedClasses());
    },

    isExpanded(eventId: string): boolean {
      return this.expandedEvents.has(eventId);
    },

    updateExpandedClasses() {
      document.querySelectorAll('.timeline-details').forEach((el) => {
        const eventId = el.closest('.timeline-event')?.getAttribute('data-event-id');
        if (eventId && this.expandedEvents.has(eventId)) {
          el.classList.add('expanded');
        } else {
          el.classList.remove('expanded');
        }
      });

      document.querySelectorAll('.timeline-expand').forEach((el) => {
        const eventId = el.closest('.timeline-event')?.getAttribute('data-event-id');
        if (eventId && this.expandedEvents.has(eventId)) {
          el.classList.add('expanded');
        } else {
          el.classList.remove('expanded');
        }
      });
    },

    scrollToYear(year: number) {
      const event = document.querySelector(`[data-year="${year}"]`);
      if (event) {
        event.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    },

    getEraForYear(year: number): string {
      if (year < 1995) return 'origins';
      if (year < 2001) return 'growth';
      if (year < 2009) return 'psf';
      if (year < 2016) return 'python3';
      if (year < 2021) return 'modern';
      return 'current';
    },

    getDotClass(type: string): string {
      switch (type) {
        case 'release':
          return 'major';
        case 'pep':
          return 'pep';
        case 'event':
          return 'organization';
        case 'milestone':
          return 'community';
        default:
          return '';
      }
    },

    getCardClass(type: string): string {
      switch (type) {
        case 'release':
          return 'major-release';
        case 'pep':
          return 'pep-card';
        case 'event':
          return 'org-card';
        case 'milestone':
          return 'community-card';
        default:
          return '';
      }
    },

    getStats() {
      const releases = this.events.filter((e) => e.type === 'release').length;
      const peps = this.events.filter((e) => e.type === 'pep').length;
      const years = new Date().getFullYear() - 1989;
      return { releases, peps, years };
    }
  }));
});

// Export for module usage
export {};
