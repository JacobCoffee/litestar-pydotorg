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
          highlights: ['Formalized development', 'Community input', 'Transparency'],
          links: [{ label: 'PEP 1', url: 'https://peps.python.org/pep-0001/' }]
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
          highlights: ['Code style', 'Readability first', 'Industry standard'],
          links: [{ label: 'PEP 8', url: 'https://peps.python.org/pep-0008/' }]
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
          highlights: ['Design philosophy', 'import this', '19 aphorisms'],
          links: [{ label: 'PEP 20', url: 'https://peps.python.org/pep-0020/' }]
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
          highlights: ['@ syntax', 'Metaprogramming', 'Framework enabler'],
          links: [{ label: 'PEP 318', url: 'https://peps.python.org/pep-0318/' }]
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
          highlights: ['Breaking changes', 'Unicode default', 'Language cleanup'],
          links: [{ label: 'PEP 3000', url: 'https://peps.python.org/pep-3000/' }]
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
          highlights: ['Built-in venvs', 'Isolation', 'No third-party needed'],
          links: [{ label: 'PEP 405', url: 'https://peps.python.org/pep-0405/' }]
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
          highlights: ['Static typing', 'Optional annotations', 'Tool support'],
          links: [{ label: 'PEP 484', url: 'https://peps.python.org/pep-0484/' }]
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
          highlights: ['@dataclass', 'Auto-generated methods', 'Less boilerplate'],
          links: [{ label: 'PEP 557', url: 'https://peps.python.org/pep-0557/' }]
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
          highlights: ['5-member council', 'Democratic election', 'Community governance'],
          links: [{ label: 'PEP 8016', url: 'https://peps.python.org/pep-8016/' }]
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
          id: 'pep-703',
          year: 2022,
          month: 'Jan',
          title: 'PEP 703 - No-GIL Python',
          description: 'Proposal to make the Global Interpreter Lock optional, accepted for Python 3.13+.',
          type: 'pep',
          pepNumber: 703,
          details: 'This historic PEP proposes making Python truly multi-threaded by allowing the GIL to be disabled, potentially revolutionizing Python performance.',
          highlights: ['Optional GIL', 'True parallelism', 'Multi-threaded Python'],
          links: [{ label: 'PEP 703', url: 'https://peps.python.org/pep-0703/' }]
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
          id: 'pep-723',
          year: 2023,
          month: 'Aug',
          title: 'PEP 723 - Inline Script Metadata',
          description: 'Standardized way to embed dependencies and metadata in single-file Python scripts.',
          type: 'pep',
          pepNumber: 723,
          details: 'Enables tools like uv and pip to automatically install dependencies for standalone scripts.',
          highlights: ['Script dependencies', 'Single-file scripts', 'Tool support'],
          links: [{ label: 'PEP 723', url: 'https://peps.python.org/pep-0723/' }]
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
          id: 'python-3.14',
          year: 2025,
          month: 'Oct',
          title: 'Python 3.14 (Upcoming)',
          description: 'Expected to include deferred evaluation of annotations and continued no-GIL improvements.',
          type: 'release',
          version: '3.14',
          details: 'Development in progress with focus on stabilizing free-threaded Python and additional performance improvements.',
          highlights: ['PEP 649', 'No-GIL stable', 'Template strings']
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

        // Update current era based on scroll position
        const events = document.querySelectorAll('.timeline-event');
        events.forEach((event) => {
          const eventRect = event.getBoundingClientRect();
          if (eventRect.top < windowHeight / 2 && eventRect.bottom > 0) {
            const year = event.getAttribute('data-year');
            if (year) {
              if (parseInt(year) < 1995) this.currentEra = 'Origins';
              else if (parseInt(year) < 2001) this.currentEra = 'Growth';
              else if (parseInt(year) < 2009) this.currentEra = 'PSF Era';
              else if (parseInt(year) < 2016) this.currentEra = 'Python 3';
              else if (parseInt(year) < 2021) this.currentEra = 'Modern';
              else this.currentEra = 'Current';
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
