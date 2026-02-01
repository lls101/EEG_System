# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EEG (Electroencephalogram) Signal Analysis System for Parkinson's Disease detection, built on FastAPI + Vue3. The system handles EEG data management, signal preprocessing, feature extraction, and deep learning-based PD detection.

**Tech Stack:**
- **Backend:** FastAPI, Tortoise ORM, PyTorch, MNE-Python (EEG processing), NumPy, SciPy
- **Frontend:** Vue 3, TypeScript, Vite 5, Naive UI, UnoCSS, Pinia, ECharts, Plotly.js
- **Database:** SQLite (via Tortoise ORM) + Redis (caching)
- **Key Libraries:** MNE-Python for EEG signal processing, PyTorch for deep learning models

## Common Commands

### Backend Development

```bash
# Start backend server (runs on port 8001, not 8000)
python run.py

# Install dependencies
pip install -r requirements.txt
# OR using PDM (preferred)
pdm install

# Database migrations (using Aerich)
aerich init-db          # Initialize database
aerich migrate          # Create migration
aerich upgrade          # Apply migration

# Check Python code style
ruff check app/         # Lint using ruff
ruff format app/        # Format using ruff
```

### Frontend Development

```bash
cd web

# Install dependencies
pnpm install

# Development server (runs on port 9527)
pnpm dev

# Build for production
pnpm build

# Type checking
pnpm typecheck

# Lint and fix
pnpm lint
```

### Docker Deployment

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## High-Level Architecture

### Backend Architecture

The backend follows a layered architecture pattern:

1. **API Layer** (`app/api/v1/`): Route definitions organized by feature
   - `route/`: Business-specific routes (features, pd_detection)
   - `preprocess/`: EEG preprocessing routes
   - `system_manage/`: System management routes
   - `auth/`: Authentication routes

2. **Controller Layer** (`app/controllers/`): Business logic coordination
   - `eeg_controller.py`: EEG file upload, format detection, storage management
   - `preprocessing_controller.py`: Basic preprocessing (filtering, referencing, resampling)
   - `ica_controller.py`: Independent Component Analysis for artifact removal
   - `wavelet_controller.py`: Wavelet denoising (ATAR algorithm)
   - `features_controller.py`: Feature extraction orchestration
   - `pd_detection.py`: PD detection model inference coordination

3. **Core Layer** (`app/core/`): Core algorithms and utilities
   - `features/`: Feature extraction algorithms
     - `time_domain.py`: Time-domain features (mean, variance, entropy, etc.)
     - `frequency_domain.py`: Frequency-domain features (PSD, band power)
     - `time_frequency.py`: Time-frequency features (wavelet, STFT)
   - `pd_detection.py`: PyTorch CNN model for PD classification
   - `init_app.py`: Application initialization (DB, routes, middleware)

4. **Models Layer** (`app/models/`): Tortoise ORM database models
   - `system/`: System models (User, Role, Menu, Api, Log, EEGFile)
   - `preprocess/`: Preprocessing models (ICA, Wavelet configurations)

5. **Schemas Layer** (`app/schemas/`): Pydantic models for request/response validation

### Frontend Architecture

The frontend uses Vue 3 with a modular structure:

1. **Routing**: Uses `@elegant-router/vue` for file-system based routing
   - Routes are auto-generated from `web/src/views/` structure
   - See `web/src/router/elegant/routes.ts` for generated routes

2. **State Management**: Pinia stores in `web/src/store/modules/`
   - `auth/`: Authentication and user info
   - `route/`: Dynamic routing based on user permissions
   - `tab/`: Tab management for multi-page navigation

3. **Key View Modules**:
   - `eegfile/`: EEG file upload and management
   - `preprocess/`: Preprocessing interfaces (basic, ICA, wavelet)
   - `analysis/features/`: Feature extraction interface
   - `apply-model/pd/`: PD detection model application
   - `manage/`: System management (users, roles, menus)

4. **Components**: Reusable components in `web/src/components/`
   - `advanced/PlotlyChart.vue`: Plotly.js chart wrapper for EEG visualization

### Data Flow Architecture

**EEG Processing Pipeline:**
1. **Upload** → File saved to `eeg_data/` with UUID, metadata stored in DB
2. **Parse** → MNE-Python reads file, extracts channel info, sampling rate, duration
3. **Preprocess** → Filtering, referencing, resampling, montage assignment
4. **Artifact Removal** → ICA or wavelet denoising to remove artifacts
5. **Feature Extraction** → Extract time/frequency/time-frequency domain features
6. **Model Inference** → Apply CNN model for PD state classification

**Key Design Patterns:**
- Controllers use `CRUDBase` generic class for standard CRUD operations
- MNE Raw objects are loaded, processed, and saved as FIF files between steps
- File paths are stored as relative paths from `settings.EEG_STORAGE_PATH`
- Background tasks run via `BackGroundTaskMiddleware` for long operations
- API logging via custom middleware (`APILoggerMiddleware`)

### Configuration System

Settings are centralized in `app/settings/config.py`:
- Database config: `TORTOISE_ORM` (SQLite connections for system + preprocess models)
- Storage paths: `EEG_STORAGE_PATH` (default: `BASE_DIR/eeg_data/`)
- JWT config: `SECRET_KEY`, `JWT_ALGORITHM`, expiry times
- Redis: `REDIS_URL` for caching (used with `fastapi-cache2`)
- CORS: Configured for cross-origin requests

**Environment Variables**: Can override settings via `.env` file

### Authentication & Authorization

- JWT-based authentication with access + refresh tokens
- Role-based access control (RBAC): Admin (`R_ADMIN`), Super (`R_SUPER`), standard users
- Button-level permissions stored in DB and checked in frontend
- Frontend guards in `web/src/router/guard/` check route permissions
- Backend dependencies in `app/core/dependency.py` validate JWT and permissions

### EEG File Format Support

Supported formats (via MNE-Python):
- **EDF/EDF+**: European Data Format
- **BDF**: BioSemi Data Format
- **FIF**: MNE-Python native format
- **SET/FDT**: EEGLAB format
- **VHDR**: Brain Vision format
- **NDF**: Nihon Kohden format (custom parser in `app/utils/NDF2MNE/`)

File handling workflow:
1. Uploaded file saved with original name in UUID directory
2. Format detection via file extension
3. MNE loading with format-specific readers
4. Conversion to FIF format for processing steps
5. Processed files stored in same UUID directory with suffixes (_preprocessed.fif, _ica.fif, etc.)

### Deep Learning Model System

**PD Detection Model** (`app/core/pd_detection.py`):
- 3-layer 1D CNN (input → 16 → 32 → 64 channels)
- Adaptive pooling + binary classification head
- Model files stored in `app/dl_models/pd/`
- Automatically loads latest `.pt` file in directory
- Input: Epoched EEG data (channels × time_samples)
- Output: Per-epoch ON/OFF predictions with confidence scores

**Model Loading**: `PDStimulationDetector` class handles model initialization, preprocessing, and inference

### Testing

Currently minimal test coverage. One test file exists:
- `test_model_load.py`: Tests model loading functionality

When adding tests, follow these patterns:
- Place backend tests in `tests/` directory (create if needed)
- Use pytest as the test framework
- Mock external dependencies (MNE file I/O, Redis, etc.)

## Important Notes for Development

1. **Port Configuration**: Backend runs on port 8001 (not 8000), frontend on 9527
2. **Database Migrations**: Use Aerich for DB changes. Always create migration before modifying models.
3. **EEG File Processing**: Always use MNE-Python's context managers for file I/O to ensure proper cleanup
4. **Async Operations**: Controllers are async; use `await` for DB operations and I/O
5. **File Storage**: All EEG data stored in UUID-based directories under `eeg_data/`, never hardcode paths
6. **Frontend Route Generation**: Modify files in `web/src/views/` to update routes, then run `pnpm gen-route`
7. **API Documentation**: Available at `http://localhost:8001/docs` (Swagger) and `/redoc` (ReDoc)
8. **Default Credentials**: admin/123456 (change in production)

## Dependencies Management

**Backend**:
- Primary: Use `pdm install` (recommended) or `pip install -r requirements.txt`
- Requirements managed in `pyproject.toml` and `requirements.txt` is auto-generated
- PyPI mirror: Tsinghua University mirror configured by default

**Frontend**:
- Uses pnpm workspaces (monorepo structure with `@sa/*` packages)
- Requires Node.js 18+ and pnpm 8+
- Lock file: `pnpm-lock.yaml` (commit this file)

## Key File Paths

- Backend entry: `run.py` (imports from `app/__init__.py`)
- Frontend entry: `web/src/main.ts`
- API routes: `app/api/__init__.py` (aggregates all v1 routes)
- Settings: `app/settings/config.py`
- Database file: `app_system.sqlite3`
- EEG storage: `eeg_data/` (created at runtime)
- Deep learning models: `app/dl_models/pd/`
