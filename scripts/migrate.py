#!/usr/bin/env python3
"""
Migration script to help transition from old structure to new structure.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any


class ProjectMigrator:
    """Handles migration from old structure to new structure."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_old_structure"
    
    def migrate(self) -> bool:
        """Run the full migration process."""
        print("🚀 Starting APIKEY-king project migration...")
        
        try:
            # Step 1: Create backup of old files
            print("\n📦 Creating backup of old files...")
            self._create_backup()
            
            # Step 2: Migrate configuration files
            print("\n⚙️ Migrating configuration...")
            self._migrate_configuration()
            
            # Step 3: Migrate query files
            print("\n🔍 Migrating query files...")
            self._migrate_queries()
            
            # Step 4: Clean up old files (optional)
            print("\n🧹 Cleaning up old files...")
            self._cleanup_old_files()
            
            print("\n✅ Migration completed successfully!")
            print(f"📁 Old files backed up to: {self.backup_dir}")
            print("\n🎯 Next steps:")
            print("1. Install new dependencies: uv pip install -r pyproject.toml")
            print("2. Run tests: pytest")
            print("3. Start with new CLI: python -m src.main --mode compatible")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create backup of old files."""
        old_files = [
            "app/hajimi_king.py",
            "common/config.py", 
            "common/Logger.py",
            "utils/github_client.py",
            "utils/file_manager.py",
            "gemini_scanner.py",
            "modelscope_scanner.py", 
            "openrouter_scanner.py",
            "start_openrouter_only.py"  # if exists
        ]
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir()
        
        for file_path in old_files:
            source = self.project_root / file_path
            if source.exists():
                dest = self.backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                print(f"  ✓ Backed up {file_path}")
        
        # Backup old query and config files
        for pattern in ["queries.*.txt", ".env.*"]:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    dest = self.backup_dir / file_path.name
                    shutil.copy2(file_path, dest)
                    print(f"  ✓ Backed up {file_path.name}")
    
    def _migrate_configuration(self) -> None:
        """Migrate old .env configuration to new format."""
        # Copy main .env to new location (if exists)
        old_env = self.project_root / ".env"
        if old_env.exists():
            print("  ✓ Keeping existing .env file")
        
        # Copy .env.template (should already be updated)
        print("  ✓ Configuration template is ready")
        
        # The new ConfigService will automatically handle old environment variables
        print("  ✓ Configuration migration compatible with old format")
    
    def _migrate_queries(self) -> None:
        """Migrate old query files to new structure."""
        query_files = {
            "queries.gemini.txt": "config/queries/gemini.txt",
            "queries.modelscope.txt": "config/queries/modelscope.txt", 
            "queries.openrouter.txt": "config/queries/openrouter.txt",
            "queries.openrouter.optimized.txt": "config/queries/openrouter.txt"
        }
        
        for old_file, new_file in query_files.items():
            old_path = self.project_root / old_file
            new_path = self.project_root / new_file
            
            if old_path.exists():
                # Ensure target directory exists
                new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy content (merge if target exists)
                if new_path.exists():
                    print(f"  ⚠️  {new_file} already exists, skipping {old_file}")
                else:
                    shutil.copy2(old_path, new_path)
                    print(f"  ✓ Migrated {old_file} -> {new_file}")
        
        # Copy main queries file to data directory
        main_queries = self.project_root / "queries.template"
        data_queries = self.project_root / "data" / "queries.txt"
        
        if main_queries.exists() and not data_queries.exists():
            data_queries.parent.mkdir(exist_ok=True)
            shutil.copy2(main_queries, data_queries)
            print(f"  ✓ Created data/queries.txt from template")
    
    def _cleanup_old_files(self) -> None:
        """Clean up old files after migration."""
        # Files to remove
        files_to_remove = [
            "gemini_scanner.py",
            "modelscope_scanner.py",
            "openrouter_scanner.py"
        ]
        
        # Directories that might be empty after migration
        dirs_to_check = [
            "app",  # Only if it just had hajimi_king.py
        ]
        
        print("  ⚠️  Old files have been backed up.")
        print("  ℹ️  You can manually remove them after verifying the new system works:")
        
        for file_path in files_to_remove:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"    - {file_path}")
        
        print("  ℹ️  Keep 'common/' and 'utils/' directories as they're still used by the new system.")


def main():
    """Main migration entry point."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    migrator = ProjectMigrator(project_root)
    success = migrator.migrate()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()