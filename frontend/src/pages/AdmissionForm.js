import React, { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { 
  User, Mail, Phone, MapPin, Calendar, Camera, Upload, 
  PenTool, CheckCircle, ArrowLeft, ArrowRight, Loader2,
  FileText, X, Lock, Eye, EyeOff
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const AdmissionForm = ({ onComplete, onUserLogin }) => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [admissionId, setAdmissionId] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    student_name: '',
    father_name: '',
    mother_name: '',
    date_of_birth: '',
    gender: '',
    contact_number: '',
    email: '',
    password: '',
    confirm_password: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    course_applying: ''
  });
  
  // File uploads
  const [photo, setPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [idProof, setIdProof] = useState(null);
  const [idProofPreview, setIdProofPreview] = useState(null);
  const [signature, setSignature] = useState(null);
  
  // Camera and signature refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const signatureCanvasRef = useRef(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });

  const courses = [
    'JEE Main 2025',
    'JEE Advanced 2025',
    'JEE Main + Advanced 2025',
    'JEE Foundation (Class 11)',
    'JEE Foundation (Class 12)',
    'JEE Crash Course'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Camera functions
  const openCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user', width: 640, height: 480 } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsCameraOpen(true);
      }
    } catch (error) {
      console.error('Camera error:', error);
      toast.error('Could not access camera. Please use file upload.');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      canvasRef.current.width = 320;
      canvasRef.current.height = 240;
      context.drawImage(videoRef.current, 0, 0, 320, 240);
      
      const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.8);
      setPhoto(dataUrl);
      setPhotoPreview(dataUrl);
      
      // Stop camera
      const stream = videoRef.current.srcObject;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      setIsCameraOpen(false);
    }
  };

  const closeCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
    }
    setIsCameraOpen(false);
  };

  const handleFileUpload = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (type === 'photo') {
          setPhoto(reader.result);
          setPhotoPreview(reader.result);
        } else if (type === 'idProof') {
          setIdProof(reader.result);
          setIdProofPreview(file.name);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Signature functions
  const initSignature = useCallback(() => {
    const canvas = signatureCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, []);

  const startDrawing = (e) => {
    setIsDrawing(true);
    const pos = getPosition(e);
    setLastPos(pos);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = signatureCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const pos = getPosition(e);
    
    ctx.beginPath();
    ctx.moveTo(lastPos.x, lastPos.y);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    
    setLastPos(pos);
  };

  const stopDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      const canvas = signatureCanvasRef.current;
      setSignature(canvas.toDataURL('image/png'));
    }
  };

  const getPosition = (e) => {
    const canvas = signatureCanvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    if (e.touches) {
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top
      };
    }
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  };

  const clearSignature = () => {
    setSignature(null);
    initSignature();
  };

  const validateStep = (stepNum) => {
    if (stepNum === 1) {
      if (!formData.student_name || !formData.father_name || !formData.date_of_birth || 
          !formData.gender || !formData.contact_number || !formData.email ||
          !formData.password || !formData.confirm_password) {
        toast.error('Please fill all required fields');
        return false;
      }
      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        toast.error('Please enter a valid email address');
        return false;
      }
      // Phone validation
      if (formData.contact_number.length < 10) {
        toast.error('Please enter a valid contact number');
        return false;
      }
      // Password validation
      if (formData.password.length < 6) {
        toast.error('Password must be at least 6 characters');
        return false;
      }
      if (formData.password !== formData.confirm_password) {
        toast.error('Passwords do not match');
        return false;
      }
    }
    if (stepNum === 2) {
      if (!formData.address || !formData.city || !formData.state || !formData.pincode || !formData.course_applying) {
        toast.error('Please fill all required fields');
        return false;
      }
    }
    if (stepNum === 3) {
      if (!photo) {
        toast.error('Please upload or capture your photo');
        return false;
      }
    }
    if (stepNum === 4) {
      if (!signature) {
        toast.error('Please add your digital signature');
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep(step)) {
      setStep(step + 1);
      if (step + 1 === 4) {
        setTimeout(initSignature, 100);
      }
    }
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(4)) return;
    
    setIsSubmitting(true);
    
    try {
      const payload = {
        ...formData,
        photo_base64: photo,
        id_proof_base64: idProof,
        signature_base64: signature
      };
      // Remove confirm_password from payload
      delete payload.confirm_password;
      
      const response = await api.post('/admissions/submit', payload);
      
      if (response.data.success) {
        setAdmissionId(response.data.admission_id);
        setIsSuccess(true);
        
        // Auto-login: Set user data and redirect to dashboard
        if (response.data.user && onUserLogin) {
          onUserLogin(response.data.user);
        }
        
        toast.success('Welcome to JEE Master! Your account has been created.');
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      }
    } catch (error) {
      console.error('Submission error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to submit form. Please try again.';
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success screen
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <Card className="max-w-md w-full shadow-2xl">
          <CardContent className="pt-8 pb-8 text-center space-y-6">
            <div className="mx-auto bg-green-100 p-4 rounded-full w-fit">
              <CheckCircle className="h-16 w-16 text-green-600" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-green-800">Welcome to JEE Master!</h2>
              <p className="text-gray-600">Your account has been created and you're now logged in.</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Your Admission ID</p>
              <p className="text-2xl font-mono font-bold text-green-700">{admissionId}</p>
            </div>
            <p className="text-sm text-gray-500">
              A confirmation email has been sent to your email address.
            </p>
            <div className="flex items-center justify-center gap-2 text-blue-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Redirecting to your dashboard...</span>
            </div>
            <Button 
              onClick={() => navigate('/dashboard')}
              className="w-full"
              data-testid="go-to-dashboard-btn"
            >
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">JEE Master Admission</h1>
          <p className="text-gray-600 mt-2">Complete your admission form in 4 easy steps</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          {[1, 2, 3, 4].map((s) => (
            <React.Fragment key={s}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {step > s ? <CheckCircle className="h-5 w-5" /> : s}
              </div>
              {s < 4 && (
                <div className={`w-16 h-1 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>

        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle>
              {step === 1 && 'Personal Details'}
              {step === 2 && 'Address & Course'}
              {step === 3 && 'Upload Documents'}
              {step === 4 && 'Digital Signature'}
            </CardTitle>
            <CardDescription>
              {step === 1 && 'Enter your personal information'}
              {step === 2 && 'Enter your address and select course'}
              {step === 3 && 'Upload your photo and ID proof'}
              {step === 4 && 'Sign digitally to complete your application'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Step 1: Personal Details */}
            {step === 1 && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="student_name">Student Name *</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="student_name"
                        name="student_name"
                        value={formData.student_name}
                        onChange={handleInputChange}
                        placeholder="Enter full name"
                        className="pl-10"
                        data-testid="student-name-input"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="date_of_birth">Date of Birth *</Label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="date_of_birth"
                        name="date_of_birth"
                        type="date"
                        value={formData.date_of_birth}
                        onChange={handleInputChange}
                        className="pl-10"
                        data-testid="dob-input"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="father_name">Father's Name *</Label>
                    <Input
                      id="father_name"
                      name="father_name"
                      value={formData.father_name}
                      onChange={handleInputChange}
                      placeholder="Father's full name"
                      data-testid="father-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="mother_name">Mother's Name</Label>
                    <Input
                      id="mother_name"
                      name="mother_name"
                      value={formData.mother_name}
                      onChange={handleInputChange}
                      placeholder="Mother's full name"
                      data-testid="mother-name-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Gender *</Label>
                  <div className="flex gap-4">
                    {['Male', 'Female', 'Other'].map((g) => (
                      <label key={g} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="gender"
                          value={g}
                          checked={formData.gender === g}
                          onChange={handleInputChange}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span>{g}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="contact_number">Contact Number *</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="contact_number"
                        name="contact_number"
                        type="tel"
                        value={formData.contact_number}
                        onChange={handleInputChange}
                        placeholder="10-digit mobile number"
                        className="pl-10"
                        maxLength={10}
                        data-testid="contact-input"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address *</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        placeholder="your@email.com"
                        className="pl-10"
                        data-testid="email-input"
                      />
                    </div>
                  </div>
                </div>

                {/* Password fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="password">Create Password *</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={handleInputChange}
                        placeholder="Min 6 characters"
                        className="pl-10 pr-10"
                        data-testid="password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm Password *</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="confirm_password"
                        name="confirm_password"
                        type={showConfirmPassword ? "text" : "password"}
                        value={formData.confirm_password}
                        onChange={handleInputChange}
                        placeholder="Confirm password"
                        className="pl-10 pr-10"
                        data-testid="confirm-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Address & Course */}
            {step === 2 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="address">Address *</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <textarea
                      id="address"
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      placeholder="Enter your full address"
                      className="w-full min-h-[80px] pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      data-testid="address-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city">City *</Label>
                    <Input
                      id="city"
                      name="city"
                      value={formData.city}
                      onChange={handleInputChange}
                      placeholder="City"
                      data-testid="city-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="state">State *</Label>
                    <Input
                      id="state"
                      name="state"
                      value={formData.state}
                      onChange={handleInputChange}
                      placeholder="State"
                      data-testid="state-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="pincode">Pincode *</Label>
                    <Input
                      id="pincode"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleInputChange}
                      placeholder="6-digit pincode"
                      maxLength={6}
                      data-testid="pincode-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="course_applying">Course Applying For *</Label>
                  <select
                    id="course_applying"
                    name="course_applying"
                    value={formData.course_applying}
                    onChange={handleInputChange}
                    className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="course-select"
                  >
                    <option value="">Select a course</option>
                    {courses.map((course) => (
                      <option key={course} value={course}>{course}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Step 3: Upload Documents */}
            {step === 3 && (
              <div className="space-y-6">
                {/* Photo Upload */}
                <div className="space-y-3">
                  <Label>Recent Passport Photo *</Label>
                  
                  {!isCameraOpen && !photoPreview && (
                    <div className="grid grid-cols-2 gap-4">
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={openCamera}
                        className="h-24 flex flex-col gap-2"
                      >
                        <Camera className="h-8 w-8" />
                        <span>Open Camera</span>
                      </Button>
                      
                      <label className="h-24 flex flex-col gap-2 items-center justify-center border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
                        <Upload className="h-8 w-8 text-gray-400" />
                        <span className="text-sm text-gray-600">Upload from Gallery</span>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileUpload(e, 'photo')}
                          className="hidden"
                        />
                      </label>
                    </div>
                  )}

                  {isCameraOpen && (
                    <div className="space-y-3">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className="w-full max-w-sm mx-auto rounded-lg border"
                      />
                      <canvas ref={canvasRef} className="hidden" />
                      <div className="flex gap-2 justify-center">
                        <Button onClick={capturePhoto} className="gap-2">
                          <Camera className="h-4 w-4" /> Capture
                        </Button>
                        <Button variant="outline" onClick={closeCamera}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  {photoPreview && (
                    <div className="relative w-32 h-40 mx-auto">
                      <img
                        src={photoPreview}
                        alt="Preview"
                        className="w-full h-full object-cover rounded-lg border-2 border-green-500"
                      />
                      <button
                        onClick={() => { setPhoto(null); setPhotoPreview(null); }}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <Badge className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-green-500">
                        Uploaded
                      </Badge>
                    </div>
                  )}
                </div>

                {/* ID Proof Upload */}
                <div className="space-y-3">
                  <Label>ID Proof (Aadhar/PAN/School ID) - Optional</Label>
                  
                  {!idProofPreview ? (
                    <label className="flex items-center justify-center gap-2 p-6 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
                      <FileText className="h-6 w-6 text-gray-400" />
                      <span className="text-gray-600">Click to upload ID proof</span>
                      <input
                        type="file"
                        accept="image/*,.pdf"
                        onChange={(e) => handleFileUpload(e, 'idProof')}
                        className="hidden"
                      />
                    </label>
                  ) : (
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                      <FileText className="h-6 w-6 text-green-600" />
                      <span className="flex-1 text-green-800">{idProofPreview}</span>
                      <button
                        onClick={() => { setIdProof(null); setIdProofPreview(null); }}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 4: Digital Signature */}
            {step === 4 && (
              <div className="space-y-4">
                <div className="space-y-3">
                  <Label>Draw your signature below</Label>
                  <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-white">
                    <canvas
                      ref={signatureCanvasRef}
                      width={500}
                      height={200}
                      className="w-full touch-none cursor-crosshair"
                      onMouseDown={startDrawing}
                      onMouseMove={draw}
                      onMouseUp={stopDrawing}
                      onMouseLeave={stopDrawing}
                      onTouchStart={startDrawing}
                      onTouchMove={draw}
                      onTouchEnd={stopDrawing}
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-gray-500">
                      <PenTool className="h-4 w-4 inline mr-1" />
                      Use mouse or touch to sign
                    </p>
                    <Button variant="outline" size="sm" onClick={clearSignature}>
                      Clear Signature
                    </Button>
                  </div>
                </div>

                {signature && (
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <span className="text-green-800">Signature captured successfully</span>
                  </div>
                )}

                {/* Summary */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-3">Application Summary</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-gray-600">Name:</div>
                    <div className="font-medium">{formData.student_name}</div>
                    <div className="text-gray-600">Email:</div>
                    <div className="font-medium">{formData.email}</div>
                    <div className="text-gray-600">Course:</div>
                    <div className="font-medium">{formData.course_applying}</div>
                    <div className="text-gray-600">Photo:</div>
                    <div className="font-medium">{photo ? '✅ Uploaded' : '❌ Missing'}</div>
                    <div className="text-gray-600">Signature:</div>
                    <div className="font-medium">{signature ? '✅ Captured' : '❌ Missing'}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-4 border-t">
              {step > 1 ? (
                <Button variant="outline" onClick={prevStep}>
                  <ArrowLeft className="h-4 w-4 mr-2" /> Previous
                </Button>
              ) : (
                <div />
              )}
              
              {step < 4 ? (
                <Button onClick={nextStep}>
                  Next <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button 
                  onClick={handleSubmit} 
                  disabled={isSubmitting}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Submit Application
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdmissionForm;
