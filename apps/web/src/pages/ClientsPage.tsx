import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useClients, useDeleteClient, type Client } from '@/features/clients/hooks/useClients'
import { ClientFormDialog } from '@/features/clients/components/ClientFormDialog'
import { Mail, Phone, MapPin, MoreVertical, Pencil, Plus, Trash2 } from 'lucide-react'

interface ClientCardProps {
  client: Client
  onEdit: (client: Client) => void
}

function ClientCard({ client, onEdit }: ClientCardProps) {
  const deleteMutation = useDeleteClient()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (window.confirm(`Are you sure you want to delete "${client.name}"?`)) {
      try {
        await deleteMutation.mutateAsync(client.id)
      } catch (error) {
        console.error('Failed to delete client:', error)
        alert('Failed to delete client. Please try again.')
      }
    }
  }

  const handleEditClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    onEdit(client)
  }

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow group relative">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-xl font-semibold text-slate-900">{client.name}</h3>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleEditClick}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDelete} className="text-red-600">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="space-y-2 text-sm text-slate-600">
        {client.contact_info?.contact_name && (
          <p className="font-medium">{client.contact_info.contact_name}</p>
        )}
        {client.contact_info?.email && (
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            <span>{client.contact_info.email}</span>
          </div>
        )}
        {client.contact_info?.phone && (
          <div className="flex items-center gap-2">
            <Phone className="h-4 w-4" />
            <span>{client.contact_info.phone}</span>
          </div>
        )}
        {client.contact_info?.address && (
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            <span className="line-clamp-2">{client.contact_info.address}</span>
          </div>
        )}
      </div>
    </Card>
  )
}

export default function ClientsPage() {
  const { data, isLoading, error } = useClients()
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleEdit = (client: Client) => {
    setEditingClient(client)
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
    setEditingClient(null)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Clients</h1>
            <p className="mt-2 text-sm text-slate-600">
              Manage your client relationships and contacts
            </p>
          </div>
          <ClientFormDialog
            client={editingClient || undefined}
            open={isDialogOpen}
            onOpenChange={(open) => {
              setIsDialogOpen(open)
              if (!open) setEditingClient(null)
            }}
            onSuccess={handleDialogClose}
            trigger={
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Client
              </Button>
            }
          />
        </div>

        {/* Clients grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">Failed to load clients. Please try again.</p>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {data.data.map((client) => (
              <ClientCard key={client.id} client={client} onEdit={handleEdit} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-600">No clients found. Add your first client to get started.</p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
