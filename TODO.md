# TODO: BrickLayers Web Application

## Project Overview

Develop a web application that allows users to upload G-code files, apply the BrickLayers post-processing script, and download the processed G-code without requiring local Python installation or configuration.

---

## Initial Technology Decision

### Recommended Technology Stack: **Python + Flask/FastAPI (Backend) + HTML/JavaScript (Frontend)**

#### Rationale:

1. **Leverage Existing Code**: The BrickLayers script is already in Python - minimal adaptation needed
2. **Your Experience**: Strong experience with both Python and HTML/JavaScript
3. **No Node.js**: Meets your preference to avoid Node.js
4. **Rapid Development**: Flask/FastAPI are lightweight and quick to set up
5. **Deployment Options**: Easy deployment to cloud platforms (Render, Railway, PythonAnywhere, AWS, etc.)

#### Alternative Considerations:

- **Go**: Would require complete rewrite of BrickLayers logic, but offers excellent performance and easy single-binary deployment
- **Rust**: Best performance, but steepest learning curve and most development time
- **Pure Client-Side (WebAssembly)**: Could compile Python to WASM, but complex setup and limited browser support

### Recommended Initial Architecture:

```
┌─────────────────────────────────────────┐
│         Frontend (Browser)              │
│  - Simple HTML upload form              │
│  - JavaScript for UX/progress           │
│  - Download processed file              │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────┐
│      Backend (Python Flask/FastAPI)     │
│  - File upload endpoint                 │
│  - BrickLayers processing engine        │
│  - Progress reporting (WebSocket/SSE)   │
│  - File download endpoint               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      File Storage (Temporary)           │
│  - Input G-code files                   │
│  - Processed output files               │
│  - Auto-cleanup after download/timeout  │
└─────────────────────────────────────────┘
```

---

## Development Recommendations

### Phase 0: Project Setup ✅

#### 0.1 Development Environment
- [x] **0.1.1** - Initialize UV virtual environment
- [x] **0.1.2** - Install FastAPI and Uvicorn
- [x] **0.1.3** - Configure VS Code for Python development
- [x] **0.1.4** - Set up debugging configuration

#### 0.2 Code Quality Tools
- [x] **0.2.1** - Install and configure Ruff for linting
- [x] **0.2.2** - Install and configure pre-commit hooks
- [x] **0.2.3** - Configure VS Code Ruff integration
- [x] **0.2.4** - Create linting documentation

#### 0.3 Project Documentation
- [x] **0.3.1** - Create TODO.md with development roadmap
- [x] **0.3.2** - Create CHANGELOG.md
- [x] **0.3.3** - Create VSCODE_SETUP.md
- [x] **0.3.4** - Create DEV_COMMANDS.md
- [x] **0.3.5** - Create LINTING_SETUP.md

---

### Phase 1: Core Functionality (MVP - Minimum Viable Product)

**Goal**: Basic working web app with essential features

#### 1.1 Backend Development

##### 1.1.1 Extract BrickLayers Core Logic ✅

- [x] Separate CLI interface from processing engine
- [x] Create clean API for web integration
- [x] Maintain backward compatibility with existing script
- [x] Create `bricklayers_core.py` module with public API

##### 1.1.2 Choose and Set Up Web Framework ✅

- [x] Evaluate Flask vs. FastAPI
- [x] **Decision**: Choose FastAPI for built-in async and better long-term scalability
- [x] Initialize project structure with virtual environment
- [x] Set up basic FastAPI application skeleton
- [x] Configure CORS middleware with environment-based origins
- [x] Create configuration system with environment variable support
- [x] Organize project structure (routers, models, services, config)
- [x] Create health check and root endpoints
- [x] Document FastAPI structure in FASTAPI_STRUCTURE.md

##### 1.1.3 Implement File Upload Endpoint

- [x] Create `/upload` endpoint accepting multipart/form-data
- [x] Accept G-code file uploads (.gcode, .gco, .g extensions)
- [x] Validate file size (configured limit: 50MB default)
- [x] Validate file format (basic G-code validation with pattern matching)
- [x] Generate unique job IDs for tracking (UUID)
- [x] Return job ID and upload details to client
- [x] Implement FileService for file operations and validation
- [x] Add comprehensive error handling with proper HTTP status codes
- [x] Sanitize filenames to prevent security issues
- [x] Accept processing parameters (start_at_layer, extrusion_multiplier)
- [x] Queue processing job on successful upload

##### 1.1.4 Implement Processing Engine ✅

- [x] Integrate BrickLayers processor with web backend
- [x] Handle processing in background (thread pool via BackgroundTasks)
- [x] Implement timeout protection (kill long-running jobs)
- [x] Add comprehensive error handling and graceful failures
- [x] Log processing events for debugging
- [x] Provide job status tracking (pending, processing, completed, failed)
- [x] Add `/status/{job_id}` endpoint to query job status

##### 1.1.5 Implement Download Endpoint ✅

- [x] Create `/download/{job_id}` endpoint
- [x] Serve processed G-code file with streaming
- [x] Add appropriate headers for download (Content-Disposition)
- [x] Implement cleanup after successful download (remove original upload; retain processed output for re-download)
- [x] Handle file not found errors gracefully

##### 1.1.6 Temporary File Management ✅

- [x] Create temporary directory structure for uploads/outputs
- [x] Store uploaded files temporarily with job ID naming
- [x] Store processed files temporarily
- [x] Implement automatic cleanup
    - Post-download: remove original upload file
    - Periodic: background cleanup task deletes files older than retention window
- [x] Add security measures (prevent directory traversal, sanitize filenames)
- [x] Set up background task for periodic cleanup

#### 1.2 Frontend Development

##### 1.2.1 Create Upload Interface

- [ ] Build simple HTML form with file input
- [ ] Display file info (name, size) before upload
- [ ] Add drag-and-drop support (nice-to-have)
- [ ] Implement client-side file validation (size, extension)
- [ ] Style with basic CSS

##### 1.2.2 Processing Status Display

- [ ] Show upload progress bar
- [ ] Show processing status/spinner with messages
- [ ] Display processing errors clearly with user-friendly messages
- [ ] Show estimated time (if possible)
- [ ] Add cancel button for long-running jobs

##### 1.2.3 Parameter Configuration UI

- [ ] Add input for `startAtLayer` (default: 3, range: 1-10)
- [ ] Add input for `extrusionMultiplier` (default: 1.05, range: 1.0-1.2)
- [ ] Add enable/disable toggle
- [ ] Add tooltips/help text for each parameter
- [ ] Consider preset profiles (conservative, normal, aggressive)
- [ ] Validate inputs client-side

##### 1.2.4 Download Interface

- [ ] Implement auto-download when processing completes, or
- [ ] Add download button with clear CTA (Call-To-Action)
- [ ] Display output file size
- [ ] Show processing summary (time taken, layers processed)
- [ ] Add "Process Another File" button to reset form

#### 1.3 Testing & Quality

##### 1.3.1 Unit Tests (Partial)

- [x] Set up pytest framework
- [ ] Test BrickLayers processing logic (core functions)
- [ ] Test file upload validation
- [ ] Test file download response
- [ ] Test parameter validation
- [ ] Aim for >80% code coverage

##### 1.3.2 Integration Tests (Partial)

- [x] Set up test fixtures with sample G-code files
- [x] Test end-to-end file processing workflow
- [ ] Test with sample G-code files from repository
- [ ] Test error handling paths
- [ ] Test concurrent job processing

##### 1.3.3 Manual Testing Checklist

- [ ] Upload various file sizes (small, medium, large)
- [ ] Test with different slicers (PrusaSlicer, OrcaSlicer, BambuStudio)
- [ ] Test error cases (invalid files, corrupted G-code, oversized files)
- [ ] Test on different browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile devices
- [ ] Test timeout scenarios

---

### Phase 2: Enhanced User Experience

#### 2.1 Real-Time Features

##### 2.1.1 Progress Reporting

- [ ] Implement WebSocket or Server-Sent Events (SSE)
- [ ] Real-time progress updates (% complete, layer count)
- [ ] Show processing statistics (lines processed, bytes processed)
- [ ] Display current processing stage
- [ ] Update UI dynamically without polling

##### 2.1.2 Before/After Preview

- [ ] Research G-code visualization libraries
- [ ] Implement basic G-code visualization (simple 2D path viewer)
- [ ] Create side-by-side comparison view
- [ ] Highlight modifications made by BrickLayers
- [ ] Add zoom and pan controls

#### 2.2 Advanced Upload Features

##### 2.2.1 Batch Processing

- [ ] Allow upload of multiple files at once
- [ ] Implement job queue system
- [ ] Show progress for all files in queue
- [ ] Download all processed files as ZIP
- [ ] Add batch operation controls (pause, cancel all)

##### 2.2.2 Session Management

- [ ] Implement session-based job tracking
- [ ] Allow users to retrieve previous jobs (last 5-10)
- [ ] Store job metadata (timestamp, parameters, status)
- [ ] Add job history UI
- [ ] Implement "resume from history" feature

#### 2.3 UI/UX Improvements

##### 2.3.1 Responsive Design

- [ ] Implement mobile-friendly layout
- [ ] Test on various screen sizes (phone, tablet, desktop)
- [ ] Optimize touch interactions for mobile
- [ ] Ensure forms are usable on small screens

##### 2.3.2 Visual Design Enhancement

- [ ] Choose and integrate CSS framework (Tailwind or Bootstrap)
- [ ] Create cohesive color scheme and typography
- [ ] Design custom logo and branding
- [ ] Add icons for better visual communication
- [ ] Implement smooth transitions and animations

##### 2.3.3 Accessibility & Themes

- [ ] Add dark mode support with toggle
- [ ] Ensure WCAG 2.1 AA compliance
- [ ] Add keyboard navigation support
- [ ] Test with screen readers
- [ ] Add loading states and skeleton screens

---

### Phase 3: Advanced Features

#### 3.1 Advanced Processing Options

##### 3.1.1 Additional BrickLayers Parameters

- [ ] Expose `layersToIgnore` option in UI
- [ ] Expose `verbosity` option for debugging
- [ ] Create "Advanced Mode" vs "Simple Mode" toggle
- [ ] Add parameter validation and constraints
- [ ] Provide detailed documentation for each parameter

##### 3.1.2 Parameter Presets

- [ ] Implement preset system (Conservative, Normal, Aggressive)
- [ ] Allow users to save custom presets locally
- [ ] Share presets via URL with encoded parameters
- [ ] Create community-contributed preset library
- [ ] Add import/export for presets

##### 3.1.3 Multi-Script Support

- [ ] Research other popular post-processing scripts
- [ ] Design plugin architecture for scripts
- [ ] Add support for 2-3 additional scripts
- [ ] Allow chaining multiple scripts together
- [ ] Create script marketplace or library UI

#### 3.2 Analytics & Insights

##### 3.2.1 Processing Statistics

- [ ] Calculate and display before/after metrics
- [ ] Estimate print time changes
- [ ] Calculate filament usage changes
- [ ] Provide strength improvement estimates (theoretical)
- [ ] Generate downloadable processing report

##### 3.2.2 File Analysis

- [ ] Detect slicer type automatically from G-code comments
- [ ] Extract and display print settings (layer height, speed, etc.)
- [ ] Show compatibility warnings for edge cases
- [ ] Detect wall generator type (Classic vs Arachne)
- [ ] Provide optimization suggestions

#### 3.3 User Accounts (Optional)

##### 3.3.1 User Authentication

- [ ] Implement optional account creation (OAuth or email)
- [ ] Add login/logout functionality
- [ ] Create user dashboard
- [ ] Implement password reset flow

##### 3.3.2 User Features

- [ ] Save processing history (unlimited for registered users)
- [ ] Save favorite parameter presets
- [ ] Cloud storage for processed files (24-48 hours)
- [ ] Usage statistics and analytics for users
- [ ] Allow sharing of processed files with others

---

### Phase 4: Deployment & Scaling

#### 4.1 Infrastructure Setup

##### 4.1.1 Production Deployment

- [ ] Choose hosting platform (Render, Railway, AWS, DigitalOcean)
- [ ] Set up production environment
- [ ] Configure custom domain and DNS
- [ ] Set up SSL/TLS certificates (Let's Encrypt)
- [ ] Configure environment variables securely

##### 4.1.2 Monitoring & Logging

- [ ] Set up application monitoring (e.g., Sentry)
- [ ] Configure structured logging
- [ ] Set up uptime monitoring
- [ ] Create dashboard for key metrics
- [ ] Set up alerting for errors and downtime

#### 4.2 Performance Optimization

##### 4.2.1 Caching & Speed

- [ ] Implement caching where appropriate (results, static assets)
- [ ] Optimize large file handling with streaming
- [ ] Add CDN for static assets
- [ ] Implement lazy loading for heavy components
- [ ] Optimize database queries (if using database)

##### 4.2.2 Scalability Infrastructure

- [ ] Set up worker queue for processing (Celery or RQ)
- [ ] Configure Redis for queue and caching
- [ ] Implement horizontal scaling capability
- [ ] Set up load balancing if needed
- [ ] Consider object storage for files (S3, MinIO, etc.)

#### 4.3 Security Hardening

##### 4.3.1 Security Measures

- [ ] Implement rate limiting to prevent abuse (per IP)
- [ ] Add file upload security (malware scanning if needed)
- [ ] Configure CORS properly for production
- [ ] Implement input sanitization everywhere
- [ ] Enforce HTTPS in production
- [ ] Add CSRF protection
- [ ] Implement security headers (CSP, X-Frame-Options, etc.)

##### 4.3.2 Data Protection

- [ ] Encrypt sensitive data at rest
- [ ] Implement secure file deletion
- [ ] Set up regular security audits
- [ ] Create data retention policy
- [ ] Implement GDPR compliance (if needed)

---

### Phase 5: Community & Documentation

#### 5.1 Documentation

##### 5.1.1 User Documentation

- [ ] Write comprehensive how-to guide for using the web app
- [ ] Create detailed parameter explanations with examples
- [ ] Build troubleshooting guide for common issues
- [ ] Create FAQ section based on user questions
- [ ] Add video tutorials

##### 5.1.2 Developer Documentation

- [ ] Write API documentation with examples
- [ ] Create detailed setup instructions for contributors
- [ ] Document architecture and design decisions
- [ ] Write contributing guidelines
- [ ] Create code style guide

#### 5.2 Community Features

##### 5.2.1 Feedback System

- [ ] Implement in-app bug reporting
- [ ] Create feature request voting system
- [ ] Add user testimonials section
- [ ] Set up GitHub discussions or forum
- [ ] Create feedback form with analytics

##### 5.2.2 Educational Content

- [ ] Write blog posts about BrickLayers technique and science
- [ ] Create video tutorials for beginners
- [ ] Build before/after examples gallery
- [ ] Share success stories from users
- [ ] Create printable quick-start guide

##### 5.2.3 Community Engagement

- [ ] Set up Discord or forum for users
- [ ] Create social media presence
- [ ] Engage with 3D printing communities
- [ ] Participate in relevant subreddits
- [ ] Present at maker faires or conferences

---

## Technical Considerations & Best Practices

### Security

- [ ] Validate all file uploads (size, type, content)
- [ ] Sanitize all user inputs
- [ ] Implement rate limiting to prevent abuse
- [ ] Use secure file storage (temporary, auto-cleanup)
- [ ] Never execute user-provided code
- [ ] Implement CSRF protection
- [ ] Use environment variables for secrets

### Performance

- [ ] Stream large file uploads/downloads
- [ ] Process files asynchronously
- [ ] Implement job queuing for high traffic
- [ ] Set reasonable timeouts
- [ ] Monitor memory usage (G-code files can be large)
- [ ] Consider file size limits

### User Experience

- [ ] Clear error messages
- [ ] Loading indicators for all async operations
- [ ] Responsive design (mobile-friendly)
- [ ] Accessibility (WCAG 2.1 compliance)
- [ ] Browser compatibility testing

### Maintenance

- [ ] Automated testing (CI/CD)
- [ ] Logging and monitoring
- [ ] Error tracking (Sentry, etc.)
- [ ] Regular dependency updates
- [ ] Backup strategy for any persistent data

---

## Development Milestones

### Milestone 1: Local Prototype (1-2 weeks)

- Basic Flask/FastAPI server
- Simple upload/process/download flow
- BrickLayers integration
- Local testing only

### Milestone 2: Alpha Release (2-3 weeks)

- Deployed to free hosting (Render, Railway)
- Basic UI with parameter controls
- Progress reporting
- Initial user testing

### Milestone 3: Beta Release (1-2 months)

- Enhanced UI/UX
- Error handling and edge cases
- Performance optimization
- Public beta testing

### Milestone 4: Production Release (3+ months)

- Full feature set
- Comprehensive documentation
- Marketing and launch

---

## Questions to Resolve

### Before Starting Development

1. **Hosting Budget**: Free tier vs. paid hosting?
2. **User Accounts**: Required or optional?
3. **File Storage**: How long to keep files? (Recommend: auto-delete after 1-24 hours)
4. **Scale Expectations**: Personal use, small community, or public service?
5. **Monetization**: Free forever, donations, premium features?
6. **Open Source**: Will the web app be open source?
7. **Branding**: Name for the web app? (e.g., "BrickLayers Online", "G-Code Brick Studio")

### Technical Decisions

1. **File Size Limits**: 10MB? 50MB? 100MB? (impacts hosting costs)
2. **Processing Timeout**: 5 minutes? 15 minutes? (prevents resource exhaustion)
3. **Concurrent Jobs**: How many simultaneous processing jobs?
4. **Storage Backend**: Local filesystem vs. S3/cloud storage?

---

## Resources & References

### Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Flask**: https://flask.palletsprojects.com/
- **File Uploads**: https://fastapi.tiangolo.com/tutorial/request-files/
- **WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/

### Deployment Platforms

- **Render** (Recommended for beginners): https://render.com/
- **Railway**: https://railway.app/
- **PythonAnywhere**: https://www.pythonanywhere.com/
- **DigitalOcean App Platform**: https://www.digitalocean.com/products/app-platform
- **AWS Elastic Beanstalk**: https://aws.amazon.com/elasticbeanstalk/

### Inspiration

- **Online G-code Viewer**: https://gcode.ws/
- **Slic3r Online**: Similar concept, different purpose
- **Thingiverse Customizer**: Web-based 3D model customization

---

## Next Steps

1. **Validate Approach**: Review this TODO with stakeholders/users
2. **Set Up Development Environment**: Python venv, FastAPI/Flask, basic project structure
3. **Create GitHub Repository**: Initialize with .gitignore, README, LICENSE
4. **Build MVP**: Focus on core upload → process → download flow
5. **Deploy Alpha**: Get it online for early testing
6. **Iterate**: Gather feedback and improve

---

## Notes

- Start simple: Don't over-engineer the MVP
- User feedback is critical: Deploy early, get feedback often
- Security first: Even for MVP, basic security is essential
- Document as you go: Future you will thank present you
- Test with real G-code files: Use the sample files in the repository

---

**Last Updated**: 2025-11-11
**Status**: MVP In Progress
**Priority**: High (MVP Development)
