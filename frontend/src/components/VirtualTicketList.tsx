import { memo } from 'react';
import { FixedSizeList as List } from 'react-window';

interface Ticket {
  id: number;
  title: string;
  status: string;
  priority: string;
  created_at: string;
}

interface Props {
  tickets: Ticket[];
  onTicketClick: (id: number) => void;
  height: number;
}

const TicketRow = memo(({ index, style, data }: any) => {
  const { tickets, onTicketClick } = data;
  const ticket = tickets[index];

  const statusColors: Record<string, string> = {
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    pending: 'bg-orange-100 text-orange-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
  };

  const priorityColors: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-600',
    high: 'bg-orange-100 text-orange-600',
    urgent: 'bg-red-100 text-red-600',
  };

  return (
    <div
      style={style}
      onClick={() => onTicketClick(ticket.id)}
      className="cursor-pointer hover:bg-gray-50 transition-colors"
    >
      <div className="p-4 border-b">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-medium text-gray-900">{ticket.title}</h3>
            <div className="mt-1 flex items-center space-x-2">
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  statusColors[ticket.status] || statusColors.open
                }`}
              >
                {ticket.status}
              </span>
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  priorityColors[ticket.priority] || priorityColors.medium
                }`}
              >
                {ticket.priority}
              </span>
            </div>
          </div>
          <span className="text-xs text-gray-500">
            {new Date(ticket.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
});

TicketRow.displayName = 'TicketRow';

export const VirtualTicketList = memo(function VirtualTicketList({
  tickets,
  onTicketClick,
  height,
}: Props) {
  return (
    <List
      height={height}
      itemCount={tickets.length}
      itemSize={100}
      width="100%"
      itemData={{ tickets, onTicketClick }}
    >
      {TicketRow}
    </List>
  );
});
