import React, { useState, useEffect, useRef } from 'react';
import { motion, useInView, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronUp, Menu, X, Phone, Mail, MapPin, Send, Linkedin, Instagram, Youtube, MessageCircle, ExternalLink, ChevronLeft, ChevronRight, Star, GraduationCap, BookOpen, Trophy, Users, Microscope, Monitor, Award, Clock, Briefcase, Beaker, Target, Rocket } from 'lucide-react';
import axios from 'axios';
import { setPageTitle } from '../utils/pageTitle';
import VideoTestimonials from '../components/landing/VideoTestimonials';
import RealResults from '../components/landing/RealResults';
import YouTubeSection from '../components/landing/YouTubeSection';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BRAND = {
  navy: '#1B3A52', darkNavy: '#0F2537', lightNavy: '#2B4A62',
  accent: '#3B5F82', bgLight: '#F8FAFC', white: '#FFFFFF',
  textDark: '#1F2937', textLight: '#6B7280'
};

const PHOTOS = {
  arms_crossed_smile: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/y920dupq_WhatsApp%20Image%202026-03-28%20at%206.14.37%20PM%20%281%29.jpeg',
  arms_crossed_serious: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/z97bm2wd_WhatsApp%20Image%202026-03-28%20at%206.14.37%20PM.jpeg',
  thinking: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/5t5bgyqt_WhatsApp%20Image%202026-03-28%20at%206.14.36%20PM%20%282%29.jpeg',
  side_pen: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/exbynac6_WhatsApp%20Image%202026-03-28%20at%206.14.36%20PM%20%281%29.jpeg',
  writing: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/1uj5x1bn_WhatsApp%20Image%202026-03-28%20at%206.14.36%20PM.jpeg',
  thumbs_up: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/b3fm88nz_WhatsApp%20Image%202026-03-28%20at%206.14.39%20PM.jpeg',
  fist_pump: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/l4ewvm7b_WhatsApp%20Image%202026-03-28%20at%206.14.38%20PM%20%281%29.jpeg',
  back_writing: 'https://customer-assets.emergentagent.com/job_df60b21b-5f85-4f46-9aaa-aefb8e4a7093/artifacts/2um8mtua_WhatsApp%20Image%202026-03-28%20at%206.14.38%20PM.jpeg',
};

const fadeUp = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6 } } };
const stagger = { visible: { transition: { staggerChildren: 0.1 } } };

function Section({ children, className = '', id, style }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.15 });
  return (
    <motion.section ref={ref} id={id} style={style} initial="hidden" animate={isInView ? 'visible' : 'hidden'} variants={stagger} className={className}>
      {children}
    </motion.section>
  );
}

function Counter({ end, suffix = '', duration = 2 }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  useEffect(() => {
    if (!isInView) return;
    let start = 0;
    const step = end / (duration * 60);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setCount(end); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 1000 / 60);
    return () => clearInterval(timer);
  }, [isInView, end, duration]);
  return <span ref={ref}>{count}{suffix}</span>;
}

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [founderModalOpen, setFounderModalOpen] = useState(false);
  const [founderTab, setFounderTab] = useState('journey');
  const [testimonialIdx, setTestimonialIdx] = useState(0);
  const [contactForm, setContactForm] = useState({ name: '', email: '', phone: '', course: '', message: '' });
  const [contactLoading, setContactLoading] = useState(false);
  const [contactSuccess, setContactSuccess] = useState(false);

  useEffect(() => { setPageTitle(null); }, []);

  useEffect(() => {
    const onScroll = () => { setScrolled(window.scrollY > 40); setShowScrollTop(window.scrollY > 300); };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollTo = (id) => { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); setMobileMenuOpen(false); };

  const handleContact = async (e) => {
    e.preventDefault();
    setContactLoading(true);
    try {
      await axios.post(`${API}/admin/contact`, contactForm);
      setContactSuccess(true);
      setContactForm({ name: '', email: '', phone: '', course: '', message: '' });
    } catch { }
    finally { setContactLoading(false); }
  };

  const testimonials = [
    { name: 'Harshit', achievement: 'AIR 916, JEE Advanced | IIT Guwahati', text: "NexUacademy's Chemistry coaching was exceptional. The concepts were crystal clear and practice problems were JEE-level.", rating: 5 },
    { name: 'Tanishq Saxena', achievement: 'AIR 341, JEE Advanced | IIT Kharagpur', text: "Nitin Sir's teaching methodology helped me secure a top 500 rank. Highly recommended!", rating: 5 },
    { name: 'Samyak Rai', achievement: 'INCHO Qualifier | IIT Hyderabad', text: "The Olympiad preparation at NexUacademy was outstanding. Made it to INCHO!", rating: 5 },
  ];

  const navLinks = [
    { label: 'Home', target: 'hero' }, { label: 'About Us', target: 'about' },
    { label: 'Courses', target: 'courses' }, { label: 'Founder', target: 'founder' },
    { label: 'Contact', target: 'contact' }
  ];

  return (
    <div className="bg-white font-[Poppins,Inter,sans-serif] text-[#1F2937] overflow-x-hidden">
      {/* NAVBAR */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-xl shadow-lg' : 'bg-white/80 backdrop-blur-md'}`} style={{ height: 72 }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => scrollTo('hero')}>
            <img src="/nexuacademy-logo.png" alt="NexUacademy" className="h-10 w-auto" />
          </div>
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map(l => (
              <button key={l.target} onClick={() => scrollTo(l.target)}
                className="text-sm font-medium hover:text-[#1B3A52] transition-colors relative group" style={{ color: BRAND.navy }}>
                {l.label}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#1B3A52] group-hover:w-full transition-all duration-300" />
              </button>
            ))}
          </div>
          <div className="hidden md:block">
            <Link to="/login" className="px-6 py-2.5 rounded-lg text-white text-sm font-semibold transition-all hover:opacity-90 hover:-translate-y-0.5 shadow-md" style={{ background: BRAND.navy }}>
              Visit Platform
            </Link>
          </div>
          <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(true)}><Menu size={24} style={{ color: BRAND.navy }} /></button>
        </div>
      </nav>

      {/* MOBILE MENU */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={{ type: 'tween', duration: 0.3 }}
            className="fixed inset-0 z-[60] bg-white flex flex-col p-6">
            <div className="flex justify-between items-center mb-8">
              <img src="/nexuacademy-logo.png" alt="NexUacademy" className="h-10" />
              <button onClick={() => setMobileMenuOpen(false)}><X size={24} /></button>
            </div>
            <div className="flex flex-col gap-6 flex-1">
              {navLinks.map(l => (
                <button key={l.target} onClick={() => scrollTo(l.target)} className="text-lg font-medium text-left" style={{ color: BRAND.navy }}>{l.label}</button>
              ))}
            </div>
            <Link to="/login" className="px-6 py-3 rounded-lg text-white text-center font-semibold" style={{ background: BRAND.navy }}>Visit Platform</Link>
          </motion.div>
        )}
      </AnimatePresence>

      {/* HERO */}
      <section id="hero" className="min-h-screen pt-[72px] relative overflow-hidden" style={{ background: `linear-gradient(135deg, ${BRAND.navy} 0%, ${BRAND.lightNavy} 100%)` }}>
        <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M30 5l21.65 12.5v25L30 55 8.35 42.5v-25z\' fill=\'none\' stroke=\'white\' stroke-width=\'1\'/%3E%3C/svg%3E")', backgroundSize: '60px 60px' }} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 md:py-24 flex flex-col md:flex-row items-center gap-12 relative z-10">
          <div className="flex-1 text-white">
            <motion.div initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
              className="inline-block px-4 py-2 rounded-full text-sm font-medium mb-6" style={{ background: 'rgba(255,255,255,0.15)' }}>
              India's Premier Online Coaching
            </motion.div>
            <motion.h1 initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-6 tracking-tight">
              Transform Your Dreams into IIT & AIIMS Reality
            </motion.h1>
            <motion.p initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 }}
              className="text-lg md:text-xl opacity-85 leading-relaxed mb-4 max-w-xl">
              Expert-led online coaching for JEE Mains, JEE Advanced, NEET & Olympiads by IIT Kharagpur Alumni
            </motion.p>
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 0.75 }} transition={{ delay: 0.8 }}
              className="text-lg italic mb-10">
              Excellence Through Innovation & Dedication
            </motion.p>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1 }} className="flex flex-wrap gap-4 mb-10">
              <Link to="/login" className="px-8 py-4 bg-white rounded-xl text-lg font-semibold shadow-xl hover:scale-105 transition-all" style={{ color: BRAND.navy }}>
                Start Your Journey
              </Link>
              <button onClick={() => scrollTo('contact')} className="px-8 py-4 rounded-xl text-lg font-semibold border-2 border-white text-white hover:bg-white hover:text-[#1B3A52] transition-all">
                Contact Us
              </button>
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.7 }} transition={{ delay: 1.2 }} className="text-sm flex flex-wrap gap-4">
              <span>7+ Years Experience</span><span>|</span><span>1000+ Students</span><span>|</span><span>IIT Kharagpur Alumni</span>
            </motion.div>
          </div>
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.6, duration: 0.8 }}
            className="flex-shrink-0">
            <div className="w-64 h-64 md:w-80 md:h-80 rounded-full overflow-hidden border-4 border-white/30 shadow-2xl">
              <img src={PHOTOS.arms_crossed_smile} alt="Nitin Saini" className="w-full h-full object-cover" />
            </div>
          </motion.div>
        </div>
        {/* Stats */}
        <div className="max-w-5xl mx-auto px-4 pb-16 relative z-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: Users, num: 7, suffix: '+', label: 'Years Teaching' },
              { icon: GraduationCap, num: 1000, suffix: '+', label: 'Students Mentored' },
              { icon: Award, label: 'IIT KGP', text: 'IIT KGP', sublabel: 'Alumni' },
              { icon: Trophy, num: 95, suffix: '%', label: 'Success Rate' },
            ].map((s, i) => (
              <motion.div key={i} variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 1.2 + i * 0.15 }}
                className="bg-white rounded-2xl p-5 text-center shadow-lg hover:-translate-y-1 transition-transform">
                <s.icon className="mx-auto mb-2" size={32} style={{ color: BRAND.navy }} />
                <div className="text-3xl md:text-4xl font-bold" style={{ color: BRAND.navy }}>
                  {s.text || <Counter end={s.num} suffix={s.suffix} />}
                </div>
                <div className="text-sm text-gray-500">{s.sublabel || s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <Section id="about" className="py-20 md:py-28 px-4" style={{ background: BRAND.bgLight }}>
        <div className="max-w-7xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold mb-4" style={{ color: BRAND.navy }}>Why Choose NexUacademy?</h2>
            <p className="text-lg max-w-2xl mx-auto" style={{ color: BRAND.textLight }}>We combine IIT-level expertise with personalized attention</p>
          </motion.div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: GraduationCap, title: 'IIT-Trained Faculty', desc: 'Learn from IIT Kharagpur Chemistry alumni with 7+ years of proven teaching experience at India\'s top coaching institutes' },
              { icon: BookOpen, title: 'Complete Curriculum', desc: 'Full syllabus coverage for JEE Mains, JEE Advanced, NEET & Olympiads with structured learning paths and regular assessments' },
              { icon: Monitor, title: 'Online Convenience', desc: 'Study anytime, anywhere with recorded lectures, live classes, doubt-clearing sessions, and 24/7 platform access' },
              { icon: Trophy, title: 'Track Record of Success', desc: 'Thousands of students successfully placed in IITs, NITs, AIIMS and top medical colleges across India' },
              { icon: Microscope, title: 'Research Background', desc: 'Real-world research experience from Sun Pharma and IIT Kharagpur projects enhances teaching methodology' },
              { icon: Star, title: 'Personalized Mentorship', desc: 'Individual doubt clearing, one-on-one guidance, customized study plans, and dedicated mentor support for each student' },
            ].map((f, i) => (
              <motion.div key={i} variants={fadeUp}
                className="bg-white p-8 rounded-2xl shadow-sm border-2 border-transparent hover:border-[#1B3A52] hover:shadow-xl hover:-translate-y-2 transition-all duration-300 group">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform" style={{ background: `${BRAND.navy}15` }}>
                  <f.icon size={28} style={{ color: BRAND.navy }} />
                </div>
                <h3 className="text-xl font-bold mb-3" style={{ color: BRAND.navy }}>{f.title}</h3>
                <p className="leading-relaxed" style={{ color: BRAND.textLight }}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* COURSES */}
      <Section id="courses" className="py-20 md:py-28 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold mb-4" style={{ color: BRAND.navy }}>Our Courses</h2>
            <p className="text-lg max-w-2xl mx-auto" style={{ color: BRAND.textLight }}>Comprehensive coaching programs designed for success</p>
          </motion.div>
          <div className="grid md:grid-cols-2 gap-8">
            {[
              { title: 'JEE Mains Mastery', badge: 'Most Popular', desc: 'Complete preparation with focus on conceptual clarity, problem-solving techniques, and exam strategies',
                features: ['Live interactive classes', '10,000+ practice problems', 'Previous year papers', 'Weekly mock tests', 'Daily doubt clearing', 'Performance analytics'], duration: '12 Months Program', gradient: 'from-[#1B3A52] to-[#2B4A62]' },
              { title: 'JEE Advanced Excellence', desc: 'Advanced problem-solving and conceptual depth for IIT aspirants with focus on analytical thinking',
                features: ['Expert-level content', 'Advanced problem sets', 'Strategy & time management', 'IIT-specific modules', 'Personalized mentorship', 'Rank improvement'], duration: '12 Months Program', gradient: 'from-[#2B4A62] to-[#3B5F82]' },
              { title: 'NEET Success Program', desc: 'Complete NEET coaching for medical college aspirants with comprehensive Biology, Chemistry, and Physics',
                features: ['Biology, Chemistry, Physics', 'NCERT-based approach', 'Medical exam strategies', 'Chapter-wise tests', 'AIIMS-level prep', 'Rank prediction'], duration: '12 Months Program', gradient: 'from-[#1B3A52] to-[#0F2537]' },
              { title: 'Olympiad Champions', desc: 'Specialized training for national and international Olympiads with advanced problem-solving',
                features: ['NSEC, NSEP, NSEB coverage', 'Competition strategies', 'Advanced techniques', 'Expert guidance', 'International exposure', 'Scholar preparation'], duration: 'Flexible Programs', gradient: 'from-[#3B5F82] to-[#1B3A52]' },
            ].map((c, i) => (
              <motion.div key={i} variants={fadeUp} className="rounded-2xl overflow-hidden shadow-lg hover:-translate-y-2 hover:shadow-2xl transition-all duration-300 group">
                <div className={`bg-gradient-to-br ${c.gradient} p-8 relative`}>
                  {c.badge && <span className="absolute top-4 right-4 px-3 py-1 bg-white/20 text-white text-xs font-semibold rounded-full">{c.badge}</span>}
                  <h3 className="text-2xl font-bold text-white mb-2">{c.title}</h3>
                  <p className="text-white/80 text-sm">{c.desc}</p>
                </div>
                <div className="bg-white p-8">
                  <div className="space-y-2 mb-6">
                    {c.features.map((f, j) => (
                      <div key={j} className="flex items-center gap-2 text-sm">
                        <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: BRAND.navy }} />
                        <span style={{ color: BRAND.textDark }}>{f}</span>
                      </div>
                    ))}
                  </div>
                  <div className="inline-block px-4 py-2 rounded-lg text-sm font-medium mb-4" style={{ background: `${BRAND.navy}10`, color: BRAND.navy }}>{c.duration}</div>
                  <Link to="/login" className="block w-full text-center px-6 py-3 rounded-xl text-white font-semibold hover:opacity-90 transition-all" style={{ background: BRAND.navy }}>
                    Explore Course
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* FOUNDER */}
      <Section id="founder" className="py-20 md:py-28 px-4 relative" style={{ background: `linear-gradient(135deg, ${BRAND.navy} 0%, ${BRAND.lightNavy} 100%)` }}>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-12 md:gap-20">
          <motion.div variants={fadeUp} className="flex-shrink-0 flex flex-col items-center">
            <motion.div animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
              className="w-72 h-72 md:w-96 md:h-96 rounded-full overflow-hidden border-[6px] border-white shadow-2xl">
              <img src={PHOTOS.arms_crossed_serious} alt="Nitin Saini" className="w-full h-full object-cover" />
            </motion.div>
            <div className="flex gap-3 mt-8">
              {[
                { icon: Linkedin, href: 'https://www.linkedin.com/in/nitinsaini-104513112', label: 'LinkedIn' },
                { icon: Instagram, href: 'https://instagram.com/nexuacademy', label: 'Instagram' },
                { icon: Send, href: 'https://t.me/NexUacademypvtltd', label: 'Telegram' },
              ].map((s, i) => (
                <a key={i} href={s.href} target="_blank" rel="noopener noreferrer"
                  className="px-4 py-2 rounded-lg border-2 border-white/40 text-white text-sm font-medium flex items-center gap-2 hover:bg-white hover:text-[#1B3A52] transition-all">
                  <s.icon size={16} />{s.label}
                </a>
              ))}
            </div>
          </motion.div>
          <motion.div variants={fadeUp} className="flex-1 text-white">
            <p className="text-sm font-semibold tracking-widest opacity-70 uppercase mb-4">Meet Our Founder</p>
            <h2 className="text-4xl sm:text-5xl font-extrabold mb-2">Nitin Saini</h2>
            <p className="text-lg opacity-90 mb-1">B.Tech Chemistry, IIT Kharagpur (2013-2018)</p>
            <p className="text-lg opacity-90 mb-6">HOD Chemistry, Vidyamandir Classes</p>
            <div className="w-20 h-1 bg-white/40 mb-8" />
            <blockquote className="text-xl italic leading-relaxed opacity-95 mb-3">
              "Education is not just about clearing exams; it's about building a foundation for lifelong success. At NexUacademy, we nurture analytical thinking, problem-solving skills, and the confidence to achieve any goal."
            </blockquote>
            <p className="text-sm opacity-80 mb-8">&#8212; Nitin Saini</p>
            <p className="text-base opacity-85 leading-relaxed mb-8">
              With a degree in Chemistry from IIT Kharagpur and over 7 years of teaching experience as HOD Chemistry at Vidyamandir Classes, Nitin Saini has mentored over 1,000 students to success in JEE, NEET, and Olympiad examinations.
            </p>
            <div className="grid grid-cols-2 gap-4 mb-8">
              {[
                { icon: GraduationCap, title: 'IIT Kharagpur Alumni', sub: 'Chemistry, 2013-2018' },
                { icon: Briefcase, title: '7+ Years Teaching', sub: 'HOD at Vidyamandir Classes' },
                { icon: Beaker, title: 'Research Experience', sub: 'Sun Pharma & IIT KGP' },
                { icon: Trophy, title: 'Award Winner', sub: 'SDM Bahadurgarh Recognition' },
              ].map((h, i) => (
                <div key={i} className="p-4 rounded-xl border border-white/20" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <h.icon size={24} className="mb-2 opacity-80" />
                  <p className="font-semibold text-sm">{h.title}</p>
                  <p className="text-xs opacity-70">{h.sub}</p>
                </div>
              ))}
            </div>
            <button onClick={() => setFounderModalOpen(true)}
              className="px-8 py-4 bg-white rounded-xl text-lg font-bold shadow-xl hover:scale-105 transition-all" style={{ color: BRAND.navy }}>
              Read Full Story
            </button>
          </motion.div>
        </div>
      </Section>

      {/* TESTIMONIALS */}
      <Section id="testimonials" className="py-20 md:py-28 px-4" style={{ background: BRAND.bgLight }}>
        <div className="max-w-5xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold mb-4" style={{ color: BRAND.navy }}>Success Stories</h2>
            <p className="text-lg" style={{ color: BRAND.textLight }}>Hear from students who achieved their dreams</p>
          </motion.div>
          <div className="relative">
            <div className="overflow-hidden">
              <motion.div key={testimonialIdx} initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }}
                className="bg-white rounded-2xl p-8 md:p-12 shadow-lg text-center max-w-2xl mx-auto">
                <div className="text-6xl opacity-10 font-serif mb-4" style={{ color: BRAND.navy }}>"</div>
                <div className="flex justify-center gap-1 mb-6">
                  {[...Array(testimonials[testimonialIdx].rating)].map((_, i) => <Star key={i} size={20} fill={BRAND.navy} style={{ color: BRAND.navy }} />)}
                </div>
                <p className="text-lg italic leading-relaxed mb-6" style={{ color: BRAND.textDark }}>"{testimonials[testimonialIdx].text}"</p>
                <p className="text-lg font-bold" style={{ color: BRAND.navy }}>{testimonials[testimonialIdx].name}</p>
                <p className="text-sm" style={{ color: BRAND.textLight }}>{testimonials[testimonialIdx].achievement}</p>
              </motion.div>
            </div>
            <div className="flex justify-center items-center gap-4 mt-8">
              <button onClick={() => setTestimonialIdx((testimonialIdx - 1 + testimonials.length) % testimonials.length)}
                className="p-2 rounded-full bg-white shadow hover:bg-gray-50"><ChevronLeft size={20} style={{ color: BRAND.navy }} /></button>
              <div className="flex gap-2">
                {testimonials.map((_, i) => (
                  <button key={i} onClick={() => setTestimonialIdx(i)}
                    className={`w-2.5 h-2.5 rounded-full transition-all ${i === testimonialIdx ? 'w-8' : ''}`}
                    style={{ background: i === testimonialIdx ? BRAND.navy : '#D1D5DB' }} />
                ))}
              </div>
              <button onClick={() => setTestimonialIdx((testimonialIdx + 1) % testimonials.length)}
                className="p-2 rounded-full bg-white shadow hover:bg-gray-50"><ChevronRight size={20} style={{ color: BRAND.navy }} /></button>
            </div>
          </div>
        </div>
      </Section>

      {/* REAL RESULTS (top achievers) */}
      <RealResults navy={BRAND.navy} />

      {/* VIDEO TESTIMONIALS */}
      <VideoTestimonials bg={BRAND.bgLight} navy={BRAND.navy} />

      {/* YOUTUBE CHANNEL */}
      <YouTubeSection navy={BRAND.navy} />

      {/* CTA */}
      <Section className="py-20 md:py-28 px-4 text-white text-center relative" style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.lightNavy})` }}>
        <div className="max-w-4xl mx-auto relative z-10">
          <motion.h2 variants={fadeUp} className="text-3xl sm:text-4xl lg:text-5xl font-extrabold mb-4">Ready to Start Your Journey to Success?</motion.h2>
          <motion.p variants={fadeUp} className="text-xl opacity-85 mb-12">Join thousands of students achieving their dreams with NexUacademy's expert guidance</motion.p>
          <motion.div variants={fadeUp} className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
            {[{ n: 1000, s: '+', l: 'Students' }, { n: 7, s: '+', l: 'Years' }, { n: 95, s: '%', l: 'Success Rate' }, { l: '24/7', text: '24/7', sublabel: 'Support' }].map((s, i) => (
              <div key={i}>
                <div className="text-4xl md:text-5xl font-bold">{s.text || <Counter end={s.n} suffix={s.s} />}</div>
                <div className="text-sm opacity-70 mt-1">{s.sublabel || s.l}</div>
              </div>
            ))}
          </motion.div>
          <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-4">
            <Link to="/login" className="px-10 py-4 bg-white rounded-xl text-lg font-bold shadow-xl hover:scale-105 transition-all" style={{ color: BRAND.navy }}>
              Explore All Courses
            </Link>
            <button onClick={() => scrollTo('contact')} className="px-10 py-4 rounded-xl text-lg font-bold border-2 border-white hover:bg-white hover:text-[#1B3A52] transition-all">
              Get in Touch
            </button>
          </motion.div>
        </div>
      </Section>

      {/* CONTACT */}
      <Section id="contact" className="py-20 md:py-28 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold mb-4" style={{ color: BRAND.navy }}>Get in Touch</h2>
            <p className="text-lg" style={{ color: BRAND.textLight }}>Have questions? We're here to help you succeed</p>
          </motion.div>
          <div className="grid md:grid-cols-[55%_45%] gap-12">
            <motion.div variants={fadeUp}>
              <div className="bg-white border-2 border-gray-100 rounded-2xl p-8 shadow-sm">
                <h3 className="text-xl font-bold mb-6" style={{ color: BRAND.navy }}>Send us a message</h3>
                {contactSuccess ? (
                  <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                    <div className="text-4xl mb-3">&#10003;</div>
                    <p className="text-green-700 font-semibold">Message sent successfully!</p>
                    <p className="text-green-600 text-sm mt-1">We'll get back to you within 24 hours.</p>
                    <button onClick={() => setContactSuccess(false)} className="mt-4 text-sm underline text-green-700">Send another message</button>
                  </div>
                ) : (
                  <form onSubmit={handleContact} className="space-y-4" data-testid="contact-form">
                    <input required value={contactForm.name} onChange={e => setContactForm({ ...contactForm, name: e.target.value })}
                      placeholder="Full Name *" className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#1B3A52] focus:ring-0 outline-none transition-colors" />
                    <input required type="email" value={contactForm.email} onChange={e => setContactForm({ ...contactForm, email: e.target.value })}
                      placeholder="Email Address *" className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#1B3A52] focus:ring-0 outline-none transition-colors" />
                    <input required value={contactForm.phone} onChange={e => setContactForm({ ...contactForm, phone: e.target.value })}
                      placeholder="Phone Number *" className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#1B3A52] focus:ring-0 outline-none transition-colors" />
                    <select required value={contactForm.course} onChange={e => setContactForm({ ...contactForm, course: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#1B3A52] focus:ring-0 outline-none transition-colors">
                      <option value="">Select a course *</option>
                      <option>JEE Mains</option><option>JEE Advanced</option><option>NEET</option><option>Olympiad Training</option><option>All Subjects</option><option>Other</option>
                    </select>
                    <textarea value={contactForm.message} onChange={e => setContactForm({ ...contactForm, message: e.target.value })}
                      placeholder="Message (Optional)" rows={3} className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#1B3A52] focus:ring-0 outline-none transition-colors resize-y" />
                    <button type="submit" disabled={contactLoading}
                      className="w-full px-6 py-3.5 rounded-xl text-white font-semibold transition-all hover:opacity-90 disabled:opacity-50"
                      style={{ background: BRAND.navy }} data-testid="contact-submit">
                      {contactLoading ? 'Sending...' : 'Send Message'}
                    </button>
                  </form>
                )}
              </div>
            </motion.div>
            <motion.div variants={fadeUp} className="space-y-4">
              {[
                { icon: Phone, label: 'Call Us', value: '+91 73558 18349', href: 'tel:+917355818349', sub: 'Mon-Sat, 9 AM - 8 PM' },
                { icon: Mail, label: 'Email Us', value: 'nexuacademypvtltd@gmail.com', href: 'mailto:nexuacademypvtltd@gmail.com', sub: "We'll respond within 24 hours" },
                { icon: MapPin, label: 'Visit Us', value: 'Dwarka, Delhi, India', sub: 'Online classes available nationwide' },
                { icon: MessageCircle, label: 'WhatsApp Channel', value: 'Join Our Community', href: 'https://whatsapp.com/channel/0029VbCqE3X23n3jMUSbCt3a' },
                { icon: Send, label: 'Telegram', value: 'Join for Updates', href: 'https://t.me/NexUacademypvtltd' },
                { icon: Instagram, label: 'Instagram', value: '@nexuacademy', href: 'https://instagram.com/nexuacademy' },
                { icon: ExternalLink, label: 'Platform', value: 'www.nexuacademy.com', href: 'https://www.nexuacademy.com' },
              ].map((c, i) => (
                <a key={i} href={c.href || '#'} target={c.href?.startsWith('http') ? '_blank' : undefined} rel="noopener noreferrer"
                  className="flex items-start gap-4 p-4 rounded-xl border-l-4 transition-all hover:bg-opacity-[0.08]"
                  style={{ borderColor: BRAND.navy, background: `${BRAND.navy}05` }}>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${BRAND.navy}10` }}>
                    <c.icon size={20} style={{ color: BRAND.navy }} />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider font-semibold" style={{ color: BRAND.textLight }}>{c.label}</p>
                    <p className="text-lg font-bold" style={{ color: BRAND.navy }}>{c.value}</p>
                    {c.sub && <p className="text-xs" style={{ color: BRAND.textLight }}>{c.sub}</p>}
                  </div>
                </a>
              ))}
              <div className="p-4 rounded-xl" style={{ background: `${BRAND.navy}05` }}>
                <p className="text-sm font-semibold mb-2" style={{ color: BRAND.navy }}>Office Hours</p>
                <p className="text-sm" style={{ color: BRAND.textLight }}>Monday - Saturday: 9:00 AM - 8:00 PM</p>
                <p className="text-sm" style={{ color: BRAND.textLight }}>Sunday: 10:00 AM - 6:00 PM</p>
              </div>
            </motion.div>
          </div>
        </div>
      </Section>

      {/* FOOTER */}
      <footer className="px-4 py-16 md:py-20" style={{ background: BRAND.darkNavy }}>
        <div className="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 text-white/70">
          <div>
            <img src="/nexuacademy-logo.png" alt="NexUacademy" className="h-14 mb-4 brightness-0 invert" />
            <p className="italic text-sm mb-4 text-white/60">Excellence Through Innovation</p>
            <p className="text-sm leading-relaxed mb-6">Transforming online coaching for JEE, NEET & Olympiad aspirants with expert guidance from IIT Kharagpur alumni.</p>
            <div className="flex gap-3">
              {[
                { icon: Linkedin, href: 'https://www.linkedin.com/in/nitinsaini-104513112' },
                { icon: Instagram, href: 'https://instagram.com/nexuacademy' },
                { icon: Youtube, href: 'https://www.youtube.com/@NexUacademypvtltd' },
                { icon: Send, href: 'https://t.me/NexUacademypvtltd' },
                { icon: MessageCircle, href: 'https://whatsapp.com/channel/0029VbCqE3X23n3jMUSbCt3a' },
              ].map((s, i) => (
                <a key={i} href={s.href} target="_blank" rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full flex items-center justify-center bg-white/10 hover:bg-[#1B3A52] transition-all">
                  <s.icon size={16} />
                </a>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-white font-bold text-lg mb-5">Quick Links</h4>
            <div className="space-y-3">
              {navLinks.map(l => (
                <button key={l.target} onClick={() => scrollTo(l.target)} className="block text-sm hover:text-white transition-colors">{l.label}</button>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-white font-bold text-lg mb-5">Our Courses</h4>
            <div className="space-y-3">
              {['JEE Mains Preparation', 'JEE Advanced Coaching', 'NEET Success Program', 'Olympiad Training', 'Chemistry Mastery'].map(c => (
                <Link key={c} to="/login" className="block text-sm hover:text-white transition-colors">{c}</Link>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-white font-bold text-lg mb-5">Get in Touch</h4>
            <div className="space-y-4 text-sm">
              <a href="tel:+917355818349" className="flex items-center gap-2 hover:text-white"><Phone size={16} /> +91 73558 18349</a>
              <a href="mailto:nexuacademypvtltd@gmail.com" className="flex items-center gap-2 hover:text-white"><Mail size={16} /> nexuacademypvtltd@gmail.com</a>
              <p className="flex items-center gap-2"><MapPin size={16} /> Dwarka, Delhi, India</p>
              <a href="https://www.nexuacademy.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-white"><ExternalLink size={16} /> www.nexuacademy.com</a>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-white/10 text-center text-white/50 text-sm">
          <p>&copy; 2026 NexUacademy. All rights reserved.</p>
          <p className="mt-2 text-xs">Made with care for aspiring engineers & doctors</p>
        </div>
      </footer>

      {/* SCROLL TO TOP */}
      <AnimatePresence>
        {showScrollTop && (
          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="fixed bottom-6 right-6 w-12 h-12 rounded-full text-white shadow-xl hover:-translate-y-1 transition-transform z-50 flex items-center justify-center"
            style={{ background: BRAND.navy }}>
            <ChevronUp size={24} />
          </motion.button>
        )}
      </AnimatePresence>

      {/* FOUNDER MODAL */}
      <AnimatePresence>
        {founderModalOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) setFounderModalOpen(false); }}>
            <motion.div initial={{ opacity: 0, y: 40, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 40 }}
              className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
              {/* Modal Header */}
              <div className="p-8 md:p-12 rounded-t-3xl relative text-white" style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.lightNavy})` }}>
                <button onClick={() => setFounderModalOpen(false)}
                  className="absolute top-4 right-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:rotate-90 transition-transform" style={{ color: BRAND.navy }}>
                  <X size={20} />
                </button>
                <div className="flex items-center gap-6">
                  <img src={PHOTOS.arms_crossed_smile} alt="Nitin Saini" className="w-24 h-24 rounded-full border-4 border-white/30 object-cover" />
                  <div>
                    <h3 className="text-3xl font-extrabold">Nitin Saini</h3>
                    <p className="opacity-80 text-sm">IIT Kharagpur Alumni | HOD Chemistry | NexUacademy Founder</p>
                  </div>
                </div>
              </div>
              {/* Tabs */}
              <div className="border-b px-4 md:px-8 flex gap-1 overflow-x-auto">
                {['journey', 'education', 'achievements', 'skills', 'philosophy'].map(t => (
                  <button key={t} onClick={() => setFounderTab(t)}
                    className={`px-4 py-4 text-sm font-semibold capitalize whitespace-nowrap border-b-3 transition-colors ${founderTab === t ? 'border-b-[3px] text-[#1B3A52]' : 'border-transparent text-gray-400 hover:text-gray-600'}`}
                    style={founderTab === t ? { borderColor: BRAND.navy } : {}}>
                    {t}
                  </button>
                ))}
              </div>
              {/* Tab Content */}
              <div className="p-6 md:p-10">
                {founderTab === 'journey' && (
                  <div className="space-y-8">
                    {[
                      { date: 'March 2026 - Present', icon: Rocket, title: 'Founder, NexUacademy', loc: 'India (Online)', desc: 'Founded NexUacademy to democratize quality JEE, NEET, and Olympiad coaching by making expert guidance accessible to every student.', badge: 'Current Venture', badgeColor: 'green' },
                      { date: 'May 2018 - Present (7+ years)', icon: Users, title: 'HOD Chemistry, Vidyamandir Classes', loc: 'Dwarka, Delhi', desc: 'Leading the Chemistry department, developing innovative curriculum. Successfully guided 1,000+ students to secure ranks in IITs, NITs, AIIMS.', stats: '1000+ Students | 95% Success Rate' },
                      { date: 'May 2016 (3 months)', icon: Microscope, title: 'Summer Research Intern, Sun Pharma', loc: 'Gurgaon, Haryana', desc: 'Gained industry experience in pharmaceutical research and development, applying theoretical chemistry knowledge to real-world drug formulation.' },
                      { date: 'May 2015 (2 months)', icon: Beaker, title: 'Research Intern, IIT Kharagpur', loc: 'IIT Kharagpur', desc: 'Synthesis of Mono- and Disubstituted Divinyl Sulfones from Glycerol Derivatives under Professor Tanmaya Pathak.' },
                    ].map((n, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: `${BRAND.navy}15` }}>
                            <n.icon size={18} style={{ color: BRAND.navy }} />
                          </div>
                          {i < 3 && <div className="w-0.5 flex-1 mt-2" style={{ background: `${BRAND.navy}20` }} />}
                        </div>
                        <div className="pb-2 flex-1">
                          <span className="text-xs font-semibold px-2 py-1 rounded" style={{ background: `${BRAND.navy}10`, color: BRAND.navy }}>{n.date}</span>
                          <h4 className="text-lg font-bold mt-2" style={{ color: BRAND.navy }}>{n.title}</h4>
                          <p className="text-xs" style={{ color: BRAND.textLight }}>{n.loc}</p>
                          <p className="text-sm mt-2 leading-relaxed" style={{ color: BRAND.textDark }}>{n.desc}</p>
                          {n.badge && <span className={`inline-block mt-2 text-xs font-semibold px-2 py-1 rounded bg-${n.badgeColor}-100 text-${n.badgeColor}-700`}>{n.badge}</span>}
                          {n.stats && <p className="text-xs font-medium mt-2" style={{ color: BRAND.navy }}>{n.stats}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {founderTab === 'education' && (
                  <div className="rounded-2xl border-l-4 p-8" style={{ borderColor: BRAND.navy, background: BRAND.bgLight }}>
                    <h3 className="text-2xl font-bold mb-1" style={{ color: BRAND.navy }}>Indian Institute of Technology, Kharagpur</h3>
                    <p className="text-lg font-semibold">Bachelor of Technology (B.Tech) - Chemistry</p>
                    <p className="text-sm mb-4" style={{ color: BRAND.textLight }}>2013 - 2018 (5 years)</p>
                    <p className="leading-relaxed mb-6" style={{ color: BRAND.textDark }}>Graduated from one of India's most prestigious technical institutions with specialized knowledge in Organic, Inorganic, and Physical Chemistry.</p>
                    <h4 className="font-bold mb-3" style={{ color: BRAND.navy }}>Key Academic Focus Areas</h4>
                    <div className="flex flex-wrap gap-2">
                      {['Advanced Organic Chemistry', 'Physical Chemistry', 'Inorganic Chemistry', 'Research Methodology', 'Analytical Skills', 'Lab Techniques', 'Scientific Communication'].map(s => (
                        <span key={s} className="px-3 py-1.5 rounded-lg text-white text-sm" style={{ background: BRAND.navy }}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {founderTab === 'achievements' && (
                  <div className="grid md:grid-cols-2 gap-6">
                    {[
                      { icon: Trophy, title: 'Award from SDM Bahadurgarh', desc: 'Recognized for outstanding contribution to education sector and positive impact on student community.' },
                      { icon: GraduationCap, title: 'IIT Kharagpur Alumni', desc: 'Graduate of one of India\'s most prestigious institutes, consistently ranked among Asia\'s top engineering colleges.' },
                      { icon: BookOpen, title: '7+ Years Teaching Excellence', desc: 'Consistent track record of producing top-ranked students in JEE and NEET examinations.' },
                      { icon: Beaker, title: 'Research Contributions', desc: 'Advanced research in organic chemistry synthesis at IIT Kharagpur and industry research at Sun Pharma.' },
                      { icon: Star, title: 'Leadership at VMC', desc: 'HOD Chemistry - developed innovative curriculum and assessment methodologies.' },
                      { icon: Rocket, title: 'Founder, NexUacademy (2026)', desc: 'Founded NexUacademy to revolutionize online coaching for competitive examinations.' },
                    ].map((a, i) => (
                      <div key={i} className="p-6 rounded-2xl border hover:shadow-md transition-shadow" style={{ borderColor: '#E5E7EB' }}>
                        <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: `${BRAND.navy}10` }}>
                          <a.icon size={28} style={{ color: BRAND.navy }} />
                        </div>
                        <h4 className="font-bold mb-2" style={{ color: BRAND.navy }}>{a.title}</h4>
                        <p className="text-sm" style={{ color: BRAND.textLight }}>{a.desc}</p>
                      </div>
                    ))}
                  </div>
                )}
                {founderTab === 'skills' && (
                  <div className="space-y-8">
                    <div>
                      <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: BRAND.navy }}><Users size={18} /> Teaching & Mentoring</h4>
                      <div className="flex flex-wrap gap-2">
                        {['JEE Mains Coaching', 'JEE Advanced Training', 'NEET Preparation', 'Olympiad Mentoring', 'Conceptual Teaching', 'Doubt Clearing', 'Student Psychology', 'Motivational Speaking'].map(s => (
                          <span key={s} className="px-3 py-1.5 rounded-lg text-sm font-medium" style={{ background: `${BRAND.navy}10`, color: BRAND.navy }}>{s}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: BRAND.navy }}><Beaker size={18} /> Chemistry Expertise</h4>
                      <div className="space-y-3">
                        {[{ label: 'Organic Chemistry', pct: 100 }, { label: 'Physical Chemistry', pct: 100 }, { label: 'Inorganic Chemistry', pct: 100 }, { label: 'Thermodynamics', pct: 95 }, { label: 'Reaction Mechanisms', pct: 100 }].map(s => (
                          <div key={s.label}>
                            <div className="flex justify-between text-sm mb-1"><span style={{ color: BRAND.textDark }}>{s.label}</span><span style={{ color: BRAND.navy }}>{s.pct}%</span></div>
                            <div className="h-2 rounded-full bg-gray-200"><div className="h-full rounded-full transition-all duration-1000" style={{ width: `${s.pct}%`, background: BRAND.navy }} /></div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {founderTab === 'philosophy' && (
                  <div className="space-y-8">
                    <div className="p-8 rounded-2xl border-l-8" style={{ background: `${BRAND.navy}05`, borderColor: BRAND.navy }}>
                      <div className="text-5xl opacity-20 font-serif" style={{ color: BRAND.navy }}>"</div>
                      <p className="text-xl italic leading-relaxed" style={{ color: BRAND.navy }}>
                        Education is not about filling a bucket, but lighting a fire. At NexUacademy, we don't just teach formulas and concepts &#8211; we ignite the passion for learning and build the confidence needed to achieve any goal.
                      </p>
                      <p className="mt-4 text-sm font-semibold" style={{ color: BRAND.textLight }}>&#8212; Nitin Saini, Founder, NexUacademy</p>
                    </div>
                    <div>
                      <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: BRAND.navy }}><Target size={18} /> Our Mission</h4>
                      <p className="leading-relaxed" style={{ color: BRAND.textDark }}>
                        To democratize quality JEE, NEET, and Olympiad coaching by making expert guidance accessible to every student, regardless of their location or economic background.
                      </p>
                    </div>
                    <div>
                      <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: BRAND.navy }}><Rocket size={18} /> Vision</h4>
                      <div className="space-y-2">
                        {['Create India\'s most trusted online coaching platform', 'Make quality education accessible to every corner of India', 'Use technology to enhance teacher-student relationships', 'Prepare students not just for exams, but for life', 'Build a community of lifelong learners'].map(v => (
                          <div key={v} className="flex items-center gap-2 text-sm" style={{ color: BRAND.textDark }}>
                            <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: BRAND.navy }} />
                            {v}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
