import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import PipelineStatus from '../PipelineStatus';
import { usePipelineWebSocket } from '@/lib/websocket';
import { api } from '@/lib/api';

// Mock dependencies
jest.mock('@/lib/websocket', () => ({
  usePipelineWebSocket: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  api: {
    getPipelineStatus: jest.fn(),
    getRunJobs: jest.fn(),
    syncPipeline: jest.fn(),
    triggerPipeline: jest.fn(),
  },
}));

const mockRuns = [
  {
    run_id: 'run-101',
    branch: 'main',
    commit_sha: 'a1b2c3d4e5',
    status: 'success',
    duration_seconds: 120,
    triggered_at: '2026-08-01T10:00:00Z',
    transport_id: 'TR-1001',
  },
  {
    run_id: 'run-102',
    branch: 'feature/sap-integration',
    commit_sha: 'f6g7h8i9j0',
    status: 'failed',
    duration_seconds: 45,
    triggered_at: '2026-08-01T11:00:00Z',
    transport_id: 'TR-1002',
  },
  {
    run_id: 'run-103',
    branch: 'fix/auth-bug',
    commit_sha: 'k1l2m3n4o5',
    status: 'running',
    duration_seconds: 30,
    triggered_at: '2026-08-01T12:00:00Z',
    transport_id: 'TR-1003',
  },
];

const mockJobs = [
  {
    name: 'Build Code',
    status: 'success',
    duration_seconds: 40,
    steps: [
      { name: 'Checkout Repository', status: 'success' },
      { name: 'Compile TypeScript', status: 'success' },
    ],
  },
  {
    name: 'Run Unit Tests',
    status: 'failed',
    duration_seconds: 60,
    steps: [
      { name: 'Setup Jest', status: 'success' },
      { name: 'Execute Test Suite', status: 'failed' },
    ],
  },
];

describe('PipelineStatus Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (usePipelineWebSocket as jest.Mock).mockReturnValue({
      data: { recent_runs: mockRuns },
      isConnected: true,
    });
    (api.getPipelineStatus as jest.Mock).mockResolvedValue({
      last_runs: mockRuns,
    });
    (api.getRunJobs as jest.Mock).mockResolvedValue(mockJobs);
  });

  test('renders correct status badge color for success/failure/running states', async () => {
    render(<PipelineStatus />);

    // Wait for the component to render runs
    expect(await screen.findByText('main')).toBeInTheDocument();
    expect(screen.getByText('feature/sap-integration')).toBeInTheDocument();
    expect(screen.getByText('fix/auth-bug')).toBeInTheDocument();

    // Verify Success badge
    const successBadge = screen.getByText('SUCCESS');
    expect(successBadge).toBeInTheDocument();
    expect(successBadge.className).toContain('badge-success');

    // Verify Failed badge
    const failedBadge = screen.getByText('FAILED');
    expect(failedBadge).toBeInTheDocument();
    expect(failedBadge.className).toContain('badge-failed');

    // Verify Running badge
    const runningBadge = screen.getByText('RUNNING');
    expect(runningBadge).toBeInTheDocument();
    expect(runningBadge.className).toContain('badge-running');
  });

  test('updates when new WebSocket data is simulated via a mock provider', async () => {
    // Start with running status for run-101
    const initialRuns = [
      {
        run_id: 'run-101',
        branch: 'main',
        commit_sha: 'a1b2c3d4e5',
        status: 'running',
        duration_seconds: 15,
        triggered_at: '2026-08-01T10:00:00Z',
      },
    ];

    (usePipelineWebSocket as jest.Mock).mockReturnValue({
      data: { recent_runs: initialRuns },
      isConnected: true,
    });

    const { rerender } = render(<PipelineStatus />);

    // Initially shows RUNNING badge
    expect(await screen.findByText('RUNNING')).toBeInTheDocument();

    // Simulate WebSocket provider emitting updated data (status changed to success)
    const updatedRuns = [
      {
        run_id: 'run-101',
        branch: 'main',
        commit_sha: 'a1b2c3d4e5',
        status: 'success',
        duration_seconds: 120,
        triggered_at: '2026-08-01T10:00:00Z',
      },
    ];

    (usePipelineWebSocket as jest.Mock).mockReturnValue({
      data: { recent_runs: updatedRuns },
      isConnected: true,
    });

    // Re-render component to simulate WebSocket state update from provider hook
    rerender(<PipelineStatus />);

    // Verify status badge updated to SUCCESS
    expect(await screen.findByText('SUCCESS')).toBeInTheDocument();
    expect(screen.queryByText('RUNNING')).not.toBeInTheDocument();
  });

  test('renders job-level breakdown correctly when a pipeline run is selected', async () => {
    render(<PipelineStatus />);

    // Click on the first pipeline run item (run-101)
    const mainBranchItem = (await screen.findByText('main')).closest('button')!;
    fireEvent.click(mainBranchItem);

    // Verify detail panel modal opens with Run Details
    expect(await screen.findByText('Run Details')).toBeInTheDocument();
    expect(screen.getByText('Jobs & Steps')).toBeInTheDocument();

    // Verify api.getRunJobs was called with run_id
    expect(api.getRunJobs).toHaveBeenCalledWith('run-101');

    // Verify jobs rendered
    expect(await screen.findByText('Build Code')).toBeInTheDocument();
    expect(screen.getByText('Run Unit Tests')).toBeInTheDocument();

    // Click to expand the first job ("Build Code")
    const buildJobBtn = screen.getByText('Build Code').closest('button')!;
    fireEvent.click(buildJobBtn);

    // Verify step breakdown inside expanded job is rendered
    expect(await screen.findByText('Checkout Repository')).toBeInTheDocument();
    expect(screen.getByText('Compile TypeScript')).toBeInTheDocument();
  });
});
