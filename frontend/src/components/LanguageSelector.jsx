import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown } from 'lucide-react';

const LanguageSelector = () => {
    const { i18n } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const languages = [
        { code: 'en', name: 'English', flag: '🇺🇸' },
        { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
        { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
        { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
        { code: 'te', name: 'Telugu', flag: '🇮🇳' },
        { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
        { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
        { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
        { code: 'ml', name: 'Malayalam', flag: '🇮🇳' },
        { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
        { code: 'ur', name: 'Urdu', flag: '🇮🇳' },
        { code: 'or', name: 'Odia', flag: '🇮🇳' },
        { code: 'as', name: 'Assamese', flag: '🇮🇳' },
        { code: 'mai', name: 'Maithili', flag: '🇮🇳' },
        { code: 'sat', name: 'Santali', flag: '🇮🇳' },
        { code: 'ks', name: 'Kashmiri', flag: '🇮🇳' },
        { code: 'ne', name: 'Nepali', flag: '🇳🇵' },
        { code: 'kok', name: 'Konkani', flag: '🇮🇳' },
        { code: 'sd', name: 'Sindhi', flag: '🇵🇰' },
        { code: 'doi', name: 'Dogri', flag: '🇮🇳' },
        { code: 'mni', name: 'Manipuri', flag: '🇮🇳' },
        { code: 'brx', name: 'Bodo', flag: '🇮🇳' },
        { code: 'sa', name: 'Sanskrit', flag: '🇮🇳' },
        { code: 'es', name: 'Spanish', flag: '🇪🇸' },
        { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
        { code: 'fr', name: 'French', flag: '🇫🇷' },
        { code: 'it', name: 'Italian', flag: '🇮🇹' },
        { code: 'ro', name: 'Romanian', flag: '🇷🇴' },
        { code: 'nl', name: 'Dutch', flag: '🇳🇱' },
        { code: 'pl', name: 'Polish', flag: '🇵🇱' },
        { code: 'hu', name: 'Hungarian', flag: '🇭🇺' },
        { code: 'cs', name: 'Czech', flag: '🇨🇿' },
        { code: 'sv', name: 'Swedish', flag: '🇸🇪' },
        { code: 'no', name: 'Norwegian', flag: '🇳🇴' },
        { code: 'da', name: 'Danish', flag: '🇩🇰' },
        { code: 'fi', name: 'Finnish', flag: '🇫🇮' },
        { code: 'de', name: 'German', flag: '🇩🇪' },
        { code: 'ru', name: 'Russian', flag: '🇷🇺' },
        { code: 'uk', name: 'Ukrainian', flag: '🇺🇦' },
        { code: 'ko', name: 'Korean', flag: '🇰🇷' },
        { code: 'fa', name: 'Persian', flag: '🇮🇷' },
        { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
        { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
        { code: 'tr', name: 'Turkish', flag: '🇹🇷' },
        { code: 'vi', name: 'Vietnamese', flag: '🇻🇳' },
        { code: 'id', name: 'Indonesian', flag: '🇮🇩' },
        { code: 'ms', name: 'Malay', flag: '🇲🇾' },
        { code: 'uz', name: 'Uzbek', flag: '🇺🇿' },
        { code: 'th', name: 'Thai', flag: '🇹🇭' },
        { code: 'lo', name: 'Lao', flag: '🇱🇦' },
        { code: 'my', name: 'Burmese', flag: '🇲🇲' },
        { code: 'tl', name: 'Tagalog', flag: '🇵🇭' },
        { code: 'sw', name: 'Swahili', flag: '🇰🇪' },
        { code: 'he', name: 'Hebrew', flag: '🇮🇱' },
        { code: 'el', name: 'Greek', flag: '🇬🇷' },
        { code: 'ar', name: 'Arabic', flag: '🇸🇦' }
    ];

    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

    const toggleDropdown = () => setIsOpen(!isOpen);

    const changeLanguage = (lng) => {
        i18n.changeLanguage(lng);
        setIsOpen(false);
    };

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={toggleDropdown}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 text-gray-700 dark:text-gray-300"
                aria-label="Select Language"
            >
                <Globe size={18} className="text-blue-500" />
                <span className="text-sm font-medium hidden sm:block">{currentLanguage.name}</span>
                <ChevronDown size={14} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-xl py-2 ring-1 ring-black ring-opacity-5 z-50 animate-in fade-in zoom-in duration-200 max-h-80 overflow-y-auto custom-scrollbar">
                    {languages.map((lang) => (
                        <button
                            key={lang.code}
                            onClick={() => changeLanguage(lang.code)}
                            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-3 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors duration-150 ${i18n.language === lang.code ? 'text-blue-600 dark:text-blue-400 font-bold bg-blue-50/50 dark:bg-blue-900/20' : 'text-gray-700 dark:text-gray-300'
                                }`}
                        >
                            <span className="text-lg">{lang.flag}</span>
                            <span>{lang.name}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default LanguageSelector;
