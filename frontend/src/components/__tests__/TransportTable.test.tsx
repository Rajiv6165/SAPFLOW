import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import TransportTable from '../TransportTable';
import { api, TransportRecord } from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  api: {
    getTransportHistory: jest.fn(),
    getLandscapes: jest.fn(),
    promoteTransport: jest.fn(),
    rollbackTransport: jest.fn(),
  },
}));

const mockTransports: TransportRecord[] = [
  {
    id: '1',
    transport_id: 'DEVK900001',
    description: 'Finance GL update',
    source_system: 'DEV',
    target_system: 'QA',
    status: 'success',
    promoted_by: 'alice',
    promoted_at: '2026-08-01T10:00:00Z',
    landscape: 'FINANCE',
  },
  {
    id: '2',
    transport_id: 'DEVK900002',
    description: 'Logistics posting fix',
    source_system: 'DEV',
    target_system: 'QA',
    status: 'pending',
    promoted_by: 'bob',
    promoted_at: '2026-08-01T11:00:00Z',
    landscape: 'LOGISTICS',
  },
  {
    id: '3',
    transport_id: 'DEVK900003',
    description: 'Sales order enhancement',
    source_system: 'QA',
    target_system: 'PROD',
    status: 'failed',
    promoted_by: 'charlie',
    promoted_at: '2026-08-01T12:00:00Z',
    landscape: 'DEFAULT',
  },
];

describe('TransportTable Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getLandscapes as jest.Mock).mockResolvedValue(['DEFAULT', 'FINANCE', 'LOGISTICS']);
    (api.getTransportHistory as jest.Mock).mockResolvedValue({
      items: mockTransports,
      page: 1,
      limit: 20,
      total: 3,
      total_pages: 1,
    });
    (api.promoteTransport as jest.Mock).mockResolvedValue({ status: 'success' });
    (api.rollbackTransport as jest.Mock).mockResolvedValue({ status: 'success' });
  });

  test('renders correct number of rows for given data', async () => {
    render(<TransportTable initialTransports={mockTransports} />);

    // Wait for elements to be present
    expect(await screen.findByText('DEVK900001')).toBeInTheDocument();
    expect(screen.getByText('DEVK900002')).toBeInTheDocument();
    expect(screen.getByText('DEVK900003')).toBeInTheDocument();

    // Verify correct number of data rows in table body
    const rows = screen.getAllByText(/DEVK90000/);
    expect(rows).toHaveLength(3);
  });

  test('shows an empty state with no data', async () => {
    (api.getTransportHistory as jest.Mock).mockResolvedValue({
      items: [],
      page: 1,
      limit: 20,
      total: 0,
      total_pages: 1,
    });

    render(<TransportTable initialTransports={[]} />);

    expect(await screen.findByText('No transports found')).toBeInTheDocument();
  });

  test('calls the rollback handler with correct transport id when rollback row action is clicked', async () => {
    const handleRollback = jest.fn().mockResolvedValue({ status: 'success' });

    render(
      <TransportTable
        initialTransports={mockTransports}
        onRollback={handleRollback}
      />
    );

    // Find row for DEVK900001 (status: success) and click its Rollback action
    const row = (await screen.findByText('DEVK900001')).closest('tr')!;
    const rollbackBtn = within(row).getByRole('button', { name: /Rollback/i });
    fireEvent.click(rollbackBtn);

    // Rollback confirmation modal should be visible
    expect(screen.getByRole('heading', { name: 'Confirm Rollback' })).toBeInTheDocument();

    // Click "Confirm Rollback" button in the modal
    const confirmBtn = screen.getByRole('button', { name: 'Confirm Rollback' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(handleRollback).toHaveBeenCalledWith('DEVK900001');
      expect(api.rollbackTransport).toHaveBeenCalledWith('DEVK900001');
    });
  });

  test('calls the promote handler with correct transport id when promote row action is clicked', async () => {
    const handlePromote = jest.fn().mockResolvedValue({ status: 'success' });

    render(
      <TransportTable
        initialTransports={mockTransports}
        onPromote={handlePromote}
      />
    );

    // Find row for DEVK900002 (status: pending) and click its Promote row action button
    const row = (await screen.findByText('DEVK900002')).closest('tr')!;
    const promoteRowBtn = within(row).getByRole('button', { name: /Promote/i });
    fireEvent.click(promoteRowBtn);

    // Modal input should be prefilled with DEVK900002
    const input = screen.getByPlaceholderText('DEVK900001') as HTMLInputElement;
    expect(input.value).toBe('DEVK900002');

    // Click "Confirm Promote" button inside the modal
    const confirmBtn = screen.getByRole('button', { name: 'Confirm Promote' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(handlePromote).toHaveBeenCalledWith(
        'DEVK900002',
        'DEV',
        'QA',
        'bob',
        'LOGISTICS'
      );
      expect(api.promoteTransport).toHaveBeenCalledWith(
        'DEVK900002',
        'DEV',
        'QA',
        'bob',
        'LOGISTICS'
      );
    });
  });
});
