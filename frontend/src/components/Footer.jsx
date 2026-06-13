import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Github, Twitter, Linkedin, Mail, MapPin, Phone, ExternalLink } from 'lucide-react';

const Footer = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const currentYear = new Date().getFullYear();

    const quickLinks = [
        { name: t('nav.home'), path: '/' },
        { name: t('nav.about'), path: '#about' },
        { name: t('nav.services'), path: '#services' },
        { name: t('nav.contact'), path: '#contact' },
    ];

    const socialLinks = [
        { icon: <Github size={20} />, url: 'https://github.com' },
        { icon: <Twitter size={20} />, url: 'https://twitter.com' },
        { icon: <Linkedin size={20} />, url: 'https://linkedin.com' },
    ];

    const handleLinkClick = (path) => {
        if (path.startsWith('#')) {
            const element = document.getElementById(path.substring(1));
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            } else {
                navigate('/');
            }
        } else {
            navigate(path);
        }
    };

    return (
        <footer className="bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-t border-white/20 dark:border-gray-800/50 pt-20 pb-12 overflow-hidden relative">
            {/* Decorative background glow */}
            <div className="absolute bottom-0 left-0 w-full h-1/2 pointer-events-none opacity-20">
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-full bg-blue-500/10 blur-[120px] rounded-full" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-full bg-purple-500/10 blur-[120px] rounded-full" />
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-16 mb-16">
                    {/* Brand Section */}
                    <div className="space-y-8">
                        <div className="flex items-center gap-4 cursor-pointer group" onClick={() => navigate('/')}>
                            <div className="w-12 h-12 relative flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                <circle cx="50" cy="50" r="38" stroke="#2D60FF" strokeWidth="8" fill="white" className="dark:fill-gray-800 shadow-xl" />
                                <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-lg" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="50" cy="50" r="38" stroke="#2D60FF" strokeWidth="8" fill="white" className="dark:fill-gray-800" />
                                    <path d="M32 62V52" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M44 62V42" stroke="#2D60FF" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M56 62V33" stroke="#4ADE80" strokeWidth="6" strokeLinecap="round" />
                                    <path d="M68 62V48" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-2xl font-black text-gray-950 dark:text-white tracking-tighter">
                                    VishwaGuru
                                </h1>
                                <p className="text-[10px] uppercase tracking-widest font-black text-blue-600 dark:text-blue-400">Civic Excellence</p>
                            </div>
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed font-medium">
                            {t('footer.description')}
                        </p>
                        <div className="flex items-center gap-4">
                            {socialLinks.map((social, index) => (
                                <a
                                    key={index}
                                    href={social.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-900 flex items-center justify-center text-gray-600 dark:text-gray-400 hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 transition-all duration-300"
                                >
                                    {social.icon}
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-gray-900 dark:text-white font-bold mb-6">{t('footer.quickLinks')}</h3>
                        <ul className="space-y-4">
                            {quickLinks.map((link) => (
                                <li key={link.name}>
                                    <button
                                        onClick={() => handleLinkClick(link.path)}
                                        className="text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 text-sm transition-colors flex items-center gap-2 group"
                                    >
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                                        {link.name}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Contact Info */}
                    <div>
                        <h3 className="text-gray-900 dark:text-white font-bold mb-6">{t('footer.contact')}</h3>
                        <ul className="space-y-4">
                            <li className="flex items-start gap-3 text-sm text-gray-500 dark:text-gray-400">
                                <MapPin className="text-blue-600 shrink-0" size={18} />
                                <span>{t('footer.address')}</span>
                            </li>
                            <li className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                                <Phone className="text-blue-600 shrink-0" size={18} />
                                <span>+91 123 456 7890</span>
                            </li>
                            <li className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                                <Mail className="text-blue-600 shrink-0" size={18} />
                                <span>contact@vishwaguru.in</span>
                            </li>
                        </ul>
                    </div>

                    {/* Newsletter / CTA */}
                    <div>
                        <h3 className="text-gray-900 dark:text-white font-bold mb-6">Stay Updated</h3>
                        <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
                            Join our newsletter for the latest civic updates.
                        </p>
                        <div className="relative">
                            <input
                                type="email"
                                placeholder="Enter email"
                                className="w-full bg-gray-100 dark:bg-gray-900 border-none rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-600 dark:text-white"
                            />
                            <button className="absolute right-2 top-2 bottom-2 bg-blue-600 text-white px-4 rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors">
                                Join
                            </button>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="border-t border-gray-100 dark:border-gray-900 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-gray-500 dark:text-gray-400 text-xs">
                        © {currentYear} VishwaGuru India. {t('footer.copyright')}
                    </p>
                    <div className="flex items-center gap-6">
                        <a href="#" className="text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 transition-colors">Privacy Policy</a>
                        <a href="#" className="text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 transition-colors">Terms of Service</a>
                        <a href="#" className="text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 transition-colors flex items-center gap-1">
                            Cookies <ExternalLink size={12} />
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
