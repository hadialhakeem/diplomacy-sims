"""
Enterprise Dependency Injection Container
Provides inversion of control and dependency management.
"""

from typing import Any, Dict, Type, TypeVar, Callable, Optional, List, Union
from abc import ABC, abstractmethod
import inspect
import threading
from enum import Enum
from dataclasses import dataclass


T = TypeVar('T')


class LifecycleScope(Enum):
    """Dependency lifecycle scopes."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class DependencyRegistration:
    """Registration information for a dependency."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifecycle: LifecycleScope = LifecycleScope.TRANSIENT
    name: Optional[str] = None


class DependencyResolutionException(Exception):
    """Raised when dependency resolution fails."""
    pass


class CircularDependencyException(DependencyResolutionException):
    """Raised when circular dependencies are detected."""
    pass


class ServiceContainer:
    """Dependency injection container with advanced features."""
    
    def __init__(self):
        self._registrations: Dict[str, DependencyRegistration] = {}
        self._singletons: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._resolution_stack: List[str] = []
        self._lock = threading.RLock()
        self._interceptors: List[Callable] = []
    
    def register_singleton(self, service_type: Type[T], 
                          implementation_type: Optional[Type[T]] = None,
                          name: Optional[str] = None) -> 'ServiceContainer':
        """Register a singleton service."""
        return self._register(service_type, implementation_type, 
                            lifecycle=LifecycleScope.SINGLETON, name=name)
    
    def register_transient(self, service_type: Type[T], 
                          implementation_type: Optional[Type[T]] = None,
                          name: Optional[str] = None) -> 'ServiceContainer':
        """Register a transient service."""
        return self._register(service_type, implementation_type, 
                            lifecycle=LifecycleScope.TRANSIENT, name=name)
    
    def register_scoped(self, service_type: Type[T], 
                       implementation_type: Optional[Type[T]] = None,
                       name: Optional[str] = None) -> 'ServiceContainer':
        """Register a scoped service."""
        return self._register(service_type, implementation_type, 
                            lifecycle=LifecycleScope.SCOPED, name=name)
    
    def register_instance(self, service_type: Type[T], instance: T,
                         name: Optional[str] = None) -> 'ServiceContainer':
        """Register a specific instance."""
        key = self._get_key(service_type, name)
        registration = DependencyRegistration(
            service_type=service_type,
            instance=instance,
            lifecycle=LifecycleScope.SINGLETON,
            name=name
        )
        
        with self._lock:
            self._registrations[key] = registration
            self._singletons[key] = instance
        
        return self
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T],
                        lifecycle: LifecycleScope = LifecycleScope.TRANSIENT,
                        name: Optional[str] = None) -> 'ServiceContainer':
        """Register a factory function."""
        key = self._get_key(service_type, name)
        registration = DependencyRegistration(
            service_type=service_type,
            factory=factory,
            lifecycle=lifecycle,
            name=name
        )
        
        with self._lock:
            self._registrations[key] = registration
        
        return self
    
    def resolve(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Resolve a service instance."""
        return self._resolve_internal(service_type, name, set())
    
    def try_resolve(self, service_type: Type[T], name: Optional[str] = None) -> Optional[T]:
        """Try to resolve a service, returning None if not registered."""
        try:
            return self.resolve(service_type, name)
        except DependencyResolutionException:
            return None
    
    def is_registered(self, service_type: Type, name: Optional[str] = None) -> bool:
        """Check if a service is registered."""
        key = self._get_key(service_type, name)
        return key in self._registrations
    
    def get_registrations(self) -> List[DependencyRegistration]:
        """Get all registrations."""
        with self._lock:
            return list(self._registrations.values())
    
    def create_scope(self) -> 'DependencyScope':
        """Create a new dependency scope."""
        return DependencyScope(self)
    
    def add_interceptor(self, interceptor: Callable[[Type, Any], Any]) -> 'ServiceContainer':
        """Add a resolution interceptor."""
        self._interceptors.append(interceptor)
        return self
    
    def _register(self, service_type: Type[T], implementation_type: Optional[Type[T]],
                 lifecycle: LifecycleScope, name: Optional[str]) -> 'ServiceContainer':
        """Internal registration method."""
        key = self._get_key(service_type, name)
        registration = DependencyRegistration(
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            lifecycle=lifecycle,
            name=name
        )
        
        with self._lock:
            self._registrations[key] = registration
        
        return self
    
    def _resolve_internal(self, service_type: Type[T], name: Optional[str], 
                         resolution_path: set) -> T:
        """Internal resolution with circular dependency detection."""
        key = self._get_key(service_type, name)
        
        # Check for circular dependencies
        if key in resolution_path:
            cycle = " -> ".join(resolution_path) + f" -> {key}"
            raise CircularDependencyException(f"Circular dependency detected: {cycle}")
        
        with self._lock:
            if key not in self._registrations:
                raise DependencyResolutionException(f"Service {service_type.__name__} not registered")
            
            registration = self._registrations[key]
            
            # Handle singleton
            if registration.lifecycle == LifecycleScope.SINGLETON:
                if key in self._singletons:
                    return self._apply_interceptors(service_type, self._singletons[key])
                
                instance = self._create_instance(registration, resolution_path.union({key}))
                self._singletons[key] = instance
                return self._apply_interceptors(service_type, instance)
            
            # Handle scoped (thread-local for now)
            elif registration.lifecycle == LifecycleScope.SCOPED:
                thread_id = str(threading.current_thread().ident)
                if thread_id not in self._scoped_instances:
                    self._scoped_instances[thread_id] = {}
                
                if key in self._scoped_instances[thread_id]:
                    return self._apply_interceptors(service_type, self._scoped_instances[thread_id][key])
                
                instance = self._create_instance(registration, resolution_path.union({key}))
                self._scoped_instances[thread_id][key] = instance
                return self._apply_interceptors(service_type, instance)
            
            # Handle transient
            else:
                instance = self._create_instance(registration, resolution_path.union({key}))
                return self._apply_interceptors(service_type, instance)
    
    def _create_instance(self, registration: DependencyRegistration, resolution_path: set) -> Any:
        """Create an instance from registration."""
        # Use provided instance
        if registration.instance is not None:
            return registration.instance
        
        # Use factory
        if registration.factory is not None:
            return registration.factory()
        
        # Use implementation type
        implementation_type = registration.implementation_type
        if implementation_type is None:
            raise DependencyResolutionException(f"No implementation for {registration.service_type.__name__}")
        
        # Resolve constructor dependencies
        return self._create_with_dependencies(implementation_type, resolution_path)
    
    def _create_with_dependencies(self, implementation_type: Type, resolution_path: set) -> Any:
        """Create instance with automatic dependency injection."""
        try:
            # Get constructor signature
            signature = inspect.signature(implementation_type.__init__)
            parameters = list(signature.parameters.values())[1:]  # Skip 'self'
            
            kwargs = {}
            for param in parameters:
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    # Try to resolve the parameter type
                    try:
                        dependency = self._resolve_internal(param.annotation, None, resolution_path)
                        kwargs[param.name] = dependency
                    except DependencyResolutionException:
                        if param.default != inspect.Parameter.empty:
                            # Use default value if resolution fails
                            continue
                        else:
                            raise DependencyResolutionException(
                                f"Cannot resolve parameter '{param.name}' of type {param.annotation}"
                            )
            
            return implementation_type(**kwargs)
            
        except Exception as e:
            raise DependencyResolutionException(f"Failed to create {implementation_type.__name__}: {str(e)}")
    
    def _apply_interceptors(self, service_type: Type, instance: Any) -> Any:
        """Apply resolution interceptors."""
        result = instance
        for interceptor in self._interceptors:
            result = interceptor(service_type, result)
        return result
    
    def _get_key(self, service_type: Type, name: Optional[str]) -> str:
        """Generate key for service registration."""
        key = f"{service_type.__module__}.{service_type.__name__}"
        if name:
            key += f":{name}"
        return key


class DependencyScope:
    """Scoped dependency container."""
    
    def __init__(self, parent: ServiceContainer):
        self.parent = parent
        self._scoped_instances: Dict[str, Any] = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._scoped_instances.clear()
    
    def resolve(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Resolve service within this scope."""
        key = self.parent._get_key(service_type, name)
        
        if key in self._scoped_instances:
            return self._scoped_instances[key]
        
        instance = self.parent.resolve(service_type, name)
        self._scoped_instances[key] = instance
        return instance


class Injectable:
    """Decorator to mark classes as injectable."""
    
    def __init__(self, lifecycle: LifecycleScope = LifecycleScope.TRANSIENT, name: Optional[str] = None):
        self.lifecycle = lifecycle
        self.name = name
    
    def __call__(self, cls):
        cls._injection_lifecycle = self.lifecycle
        cls._injection_name = self.name
        return cls


def inject(container: ServiceContainer):
    """Decorator for automatic dependency injection."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Inject dependencies based on function signature
            signature = inspect.signature(func)
            for param_name, param in signature.parameters.items():
                if param_name not in kwargs and param.annotation != inspect.Parameter.empty:
                    try:
                        dependency = container.resolve(param.annotation)
                        kwargs[param_name] = dependency
                    except DependencyResolutionException:
                        if param.default == inspect.Parameter.empty:
                            raise
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global container instance
container = ServiceContainer()
