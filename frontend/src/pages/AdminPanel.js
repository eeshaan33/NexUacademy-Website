import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { 
  Users, FileText, Download, Search, Eye, CheckCircle, XCircle,
  Clock, Filter, RefreshCw, ChevronLeft, ChevronRight, Mail, Phone
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const AdminPanel = () => {
  const [admissions, setAdmissions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAdmission, setSelectedAdmission] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchData();
  }, [filter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [admissionsRes, statsRes] = await Promise.all([
        api.get('/admissions/list', {
          params: {
            status: filter !== 'all' ? filter : undefined,
            limit: 10,
            skip: (page - 1) * 10
          }
        }),
        api.get('/admissions/stats')
      ]);
      
      setAdmissions(admissionsRes.data.admissions);
      setTotalPages(admissionsRes.data.pages);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load admissions');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdmissionDetail = async (admissionId) => {
    try {
      const response = await api.get(`/admissions/detail/${admissionId}`);
      setSelectedAdmission(response.data);
    } catch (error) {
      toast.error('Failed to load admission details');
    }
  };

  const updateStatus = async (admissionId, status) => {
    try {
      await api.put(`/admissions/update-status/${admissionId}?status=${status}`);
      toast.success(`Admission ${status}`);
      fetchData();
      setSelectedAdmission(null);
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const exportToExcel = async () => {
    try {
      const response = await api.get('/admissions/export/excel', {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'admissions.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Export downloaded successfully');
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  const filteredAdmissions = admissions.filter(a => 
    !searchQuery || 
    a.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.admission_id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-green-500"><CheckCircle className="h-3 w-3 mr-1" /> Approved</Badge>;
      case 'rejected':
        return <Badge className="bg-red-500"><XCircle className="h-3 w-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge className="bg-yellow-500"><Clock className="h-3 w-3 mr-1" /> Pending</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Admin Panel</h1>
            <p className="text-gray-600">Manage student admissions</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchData}>
              <RefreshCw className="h-4 w-4 mr-2" /> Refresh
            </Button>
            <Button onClick={exportToExcel} className="bg-green-600 hover:bg-green-700">
              <Download className="h-4 w-4 mr-2" /> Export CSV
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Applications</p>
                    <p className="text-3xl font-bold">{stats.total}</p>
                  </div>
                  <Users className="h-10 w-10 text-blue-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Pending</p>
                    <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
                  </div>
                  <Clock className="h-10 w-10 text-yellow-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Approved</p>
                    <p className="text-3xl font-bold text-green-600">{stats.approved}</p>
                  </div>
                  <CheckCircle className="h-10 w-10 text-green-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Rejected</p>
                    <p className="text-3xl font-bold text-red-600">{stats.rejected}</p>
                  </div>
                  <XCircle className="h-10 w-10 text-red-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters and Search */}
        <Card className="bg-white">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="flex gap-2">
                <Button 
                  variant={filter === 'all' ? 'default' : 'outline'}
                  onClick={() => { setFilter('all'); setPage(1); }}
                  size="sm"
                >
                  All
                </Button>
                <Button 
                  variant={filter === 'pending' ? 'default' : 'outline'}
                  onClick={() => { setFilter('pending'); setPage(1); }}
                  size="sm"
                >
                  Pending
                </Button>
                <Button 
                  variant={filter === 'approved' ? 'default' : 'outline'}
                  onClick={() => { setFilter('approved'); setPage(1); }}
                  size="sm"
                >
                  Approved
                </Button>
                <Button 
                  variant={filter === 'rejected' ? 'default' : 'outline'}
                  onClick={() => { setFilter('rejected'); setPage(1); }}
                  size="sm"
                >
                  Rejected
                </Button>
              </div>
              
              <div className="relative w-full md:w-72">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by name, email, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Admissions Table */}
        <Card className="bg-white">
          <CardHeader>
            <CardTitle>Applications</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                <p className="mt-2 text-gray-600">Loading...</p>
              </div>
            ) : filteredAdmissions.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 mx-auto text-gray-300" />
                <p className="mt-2 text-gray-600">No applications found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left p-3 font-medium">ID</th>
                      <th className="text-left p-3 font-medium">Student Name</th>
                      <th className="text-left p-3 font-medium">Course</th>
                      <th className="text-left p-3 font-medium">Contact</th>
                      <th className="text-left p-3 font-medium">Date</th>
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAdmissions.map((admission) => (
                      <tr key={admission.admission_id} className="border-b hover:bg-gray-50">
                        <td className="p-3 font-mono text-sm">{admission.admission_id}</td>
                        <td className="p-3">
                          <div className="font-medium">{admission.student_name}</div>
                          <div className="text-sm text-gray-500">{admission.email}</div>
                        </td>
                        <td className="p-3">{admission.course_applying}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-1 text-sm">
                            <Phone className="h-3 w-3" /> {admission.contact_number}
                          </div>
                        </td>
                        <td className="p-3 text-sm">
                          {new Date(admission.submitted_at).toLocaleDateString()}
                        </td>
                        <td className="p-3">{getStatusBadge(admission.status)}</td>
                        <td className="p-3">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => fetchAdmissionDetail(admission.admission_id)}
                          >
                            <Eye className="h-4 w-4 mr-1" /> View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Page {page} of {totalPages}
                </p>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(p => p - 1)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={page === totalPages}
                    onClick={() => setPage(p => p + 1)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detail Modal */}
      {selectedAdmission && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-auto">
            <CardHeader className="border-b">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Application Details</CardTitle>
                  <CardDescription>ID: {selectedAdmission.admission_id}</CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setSelectedAdmission(null)}>
                  <XCircle className="h-5 w-5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Photo and Signature */}
              <div className="flex gap-6">
                {selectedAdmission.photo && (
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-2">Photo</p>
                    <img 
                      src={selectedAdmission.photo} 
                      alt="Student" 
                      className="w-32 h-40 object-cover rounded-lg border"
                    />
                  </div>
                )}
                {selectedAdmission.signature && (
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-2">Signature</p>
                    <img 
                      src={selectedAdmission.signature} 
                      alt="Signature" 
                      className="h-20 border rounded bg-white"
                    />
                  </div>
                )}
              </div>

              {/* Personal Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Student Name</p>
                  <p className="font-medium">{selectedAdmission.student_name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Date of Birth</p>
                  <p className="font-medium">{selectedAdmission.date_of_birth}</p>
                </div>
                <div>
                  <p className="text-gray-600">Father's Name</p>
                  <p className="font-medium">{selectedAdmission.father_name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Mother's Name</p>
                  <p className="font-medium">{selectedAdmission.mother_name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Gender</p>
                  <p className="font-medium">{selectedAdmission.gender}</p>
                </div>
                <div>
                  <p className="text-gray-600">Contact</p>
                  <p className="font-medium">{selectedAdmission.contact_number}</p>
                </div>
                <div>
                  <p className="text-gray-600">Email</p>
                  <p className="font-medium">{selectedAdmission.email}</p>
                </div>
                <div>
                  <p className="text-gray-600">Course</p>
                  <p className="font-medium">{selectedAdmission.course_applying}</p>
                </div>
              </div>

              {/* Address */}
              <div>
                <p className="text-sm text-gray-600">Address</p>
                <p className="font-medium">
                  {selectedAdmission.address}, {selectedAdmission.city}, {selectedAdmission.state} - {selectedAdmission.pincode}
                </p>
              </div>

              {/* Status */}
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">Current Status:</span>
                {getStatusBadge(selectedAdmission.status)}
              </div>

              {/* Action Buttons */}
              {selectedAdmission.status === 'pending' && (
                <div className="flex gap-3 pt-4 border-t">
                  <Button 
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() => updateStatus(selectedAdmission.admission_id, 'approved')}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" /> Approve
                  </Button>
                  <Button 
                    className="flex-1 bg-red-600 hover:bg-red-700"
                    onClick={() => updateStatus(selectedAdmission.admission_id, 'rejected')}
                  >
                    <XCircle className="h-4 w-4 mr-2" /> Reject
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
