import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Trash2 } from 'lucide-react';

interface ApiKey {
  id: number;
  name: string;
  key: string;
  created_at: string;
  is_active: boolean;
}

export default function Dashboard() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');

  const fetchApiKeys = async () => {
    try {
      const response = await api.get('/api-keys');
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to fetch API keys', error);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const createApiKey = async () => {
    if (!newKeyName) return;
    try {
      await api.post('/api-keys', { name: newKeyName });
      setNewKeyName('');
      fetchApiKeys();
    } catch (error) {
      console.error('Failed to create API key', error);
    }
  };

  const deleteApiKey = async (id: number) => {
    try {
      await api.delete(`/api-keys/${id}`);
      fetchApiKeys();
    } catch (error) {
      console.error('Failed to delete API key', error);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Create API Key</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Input
            placeholder="Key Name"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <Button onClick={createApiKey}>Create</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your API Keys</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {apiKeys.map((apiKey) => (
                <TableRow key={apiKey.id}>
                  <TableCell>{apiKey.name}</TableCell>
                  <TableCell className="font-mono">{apiKey.key}</TableCell>
                  <TableCell>{new Date(apiKey.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>{apiKey.is_active ? 'Active' : 'Inactive'}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" onClick={() => deleteApiKey(apiKey.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
