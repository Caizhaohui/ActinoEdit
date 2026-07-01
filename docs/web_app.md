# ActinoEdit Web Application

## Overview

ActinoEdit includes a local web application built with NiceGUI for a user-friendly interface.

## Starting the Web App

```bash
actinoedit-web
```

This will start a local web server at `http://127.0.0.1:8080`.

## Features

### File Upload

- Upload genome FASTA files
- Upload GFF or GenBank annotation files

### Parameter Configuration

- Select organism profile
- Configure PAM pattern
- Set spacer length
- Set max mismatches

### Target Selection

- Enter locus_tag
- Enter gene name
- Enter coordinates (contig:start-end)

### Results

- Interactive guide candidate table
- Sorting and filtering
- Download CSV, Excel, HTML reports

### Demo Mode

Load example data to try the tool without uploading files.

## Development

The web application is in `src/actinoedit/web/`:

- `app.py`: Main application entry point
- `pages.py`: Page definitions
- `components.py`: Reusable UI components
- `state.py`: Application state management
- `runner.py`: Pipeline execution wrapper
